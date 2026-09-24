"""Command line entry point.

  python -m tracker run      check every job board, update data, send alerts
  python -m tracker render   rebuild README/dashboard from saved data only
  python -m tracker probe    find which job-board platform each careers page uses
  python -m tracker diagnose show what each job board returns and why roles are kept
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import sys

from . import notify, render, store
from .classify import classify
from .config import load_companies, load_search, load_watchlist
from .runner import run_all

log = logging.getLogger("tracker")
REFRESH_HOURS = 20  # rewrite files at least this often even when nothing changed


def _fingerprint(state: dict, health: dict) -> str:
    meta = {k: v for k, v in state["meta"].items() if k != "last_run"}
    return json.dumps([meta, state["jobs"], health], sort_keys=True)


def reclassify(state: dict, search) -> None:
    """Re-apply the current search rules to saved roles, so config edits take effect."""
    for jid in list(state["jobs"]):
        job = state["jobs"][jid]
        cls = classify(job["title"], search, facts=job.get("facts"),
                       in_country=job.get("in_country", True))
        if not cls.relevant:
            del state["jobs"][jid]
            continue
        job.update(category=cls.category, category_label=cls.category_label,
                   priority=cls.priority, level=cls.level, tags=cls.tags, score=cls.score)


def cmd_run(args) -> int:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    today = now.date()
    search, companies, watchlist = load_search(), load_companies(), load_watchlist()
    configured = {s.key for c in companies for s in c.sources}
    state = store.load_json(store.STATE_PATH, store.empty_state())
    health = store.load_json(store.HEALTH_PATH, {})
    before = _fingerprint(state, health)

    only = {o.strip().lower() for o in args.only.split(",")} if args.only else None
    results = run_all(companies, search, state["jobs"], only=only)
    if results and not any(r.ok for r in results):
        log.error("Every job board failed - probably a network problem. Nothing saved.")
        return 1

    reclassify(state, search)
    changes = store.merge(state, results, today, configured)
    health = store.update_health(health, results, today, configured)
    log.info("new=%d closed=%d reopened=%d added-silently=%d open=%d",
             len(changes["new"]), len(changes["closed"]), len(changes["reopened"]),
             len(changes["silent"]),
             sum(1 for j in state["jobs"].values() if j["status"] == "open"))

    if args.dry_run:
        for j in changes["new"] + changes["silent"]:
            log.info("  + %s | %s | %s | %s", j["company"], j["title"], j["category_label"], j["level"])
        return 0

    notify_on = not args.no_notify and os.environ.get("TRACKER_NOTIFY", "1") != "0"
    if notify_on:
        _send_alerts(state, changes, today)

    last_run = state["meta"].get("last_run")
    stale = (not last_run or now - dt.datetime.fromisoformat(last_run.replace("Z", "+00:00"))
             > dt.timedelta(hours=REFRESH_HOURS))
    if _fingerprint(state, health) != before or stale:
        state["meta"]["last_run"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        store.save_json(store.STATE_PATH, state)
        store.save_json(store.HEALTH_PATH, health)
        render.render_all(state, health, watchlist, now)
        log.info("Saved data and rebuilt README, dashboard and feed")
    else:
        log.info("Nothing changed; files left as they are")
    return 0


def _send_alerts(state: dict, changes: dict, today: dt.date) -> None:
    meta = state["meta"]
    date = today.strftime("%-d %b %Y")
    if not meta.get("snapshot_issue"):
        current = [j for j in state["jobs"].values()
                   if j["status"] == "open" and notify.worth_alerting(j)]
        if not current:
            return
        issue = notify.announce(
            current, f"Tracker is live: {len(current)} open roles right now ({date})",
            "These are the relevant roles open today. From now on you'll get an issue like "
            "this only when something new appears.")
        if issue:
            meta["snapshot_issue"] = issue.get("number")
        return
    fresh = [j for j in changes["new"] + changes["reopened"] if notify.worth_alerting(j)]
    if not fresh:
        return
    top = sorted(fresh, key=lambda j: (not j.get("priority"), -int(j.get("score", 0))))[0]
    more = f" + {len(fresh) - 1} more" if len(fresh) > 1 else ""
    notify.announce(fresh, f"New: {top['company']} – {top['title'][:70]}{more} ({date})",
                    f"{len(fresh)} new role{'s' if len(fresh) != 1 else ''} since the last check.")


def cmd_render(_args) -> int:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    state = store.load_json(store.STATE_PATH, store.empty_state())
    health = store.load_json(store.HEALTH_PATH, {})
    render.render_all(state, health, load_watchlist(), now)
    return 0


def cmd_diagnose(args) -> int:
    """Show what each job board returns and why each role is kept or skipped."""
    import requests

    from .sources import build_source

    search = load_search()
    only = {o.strip().lower() for o in args.only.split(",")} if args.only else None
    for company in load_companies():
        if only and company.slug not in only and company.name.lower() not in only:
            continue
        for src in company.sources:
            print(f"\n=== {company.name} [{src.key}] ===")
            try:
                source = build_source(company, src, search)
                jobs = source.fetch()
            except requests.HTTPError as exc:
                body = exc.response.text[:300] if exc.response is not None else ""
                print(f"ERROR {exc}\n{body}")
                continue
            except Exception as exc:  # noqa: BLE001
                print(f"ERROR {type(exc).__name__}: {exc}")
                continue
            where = {True: 0, None: 0, False: 0}
            for job in jobs:
                where[job.in_country] += 1
            print(f"{source.note or ''} | read {source.scanned} | returned {len(jobs)} | "
                  f"UK {where[True]} unclear {where[None]} other {where[False]}")
            kept = []
            for job in jobs:
                cls = classify(job.title, search, in_country=job.in_country)
                if cls.relevant and job.in_country is True:
                    kept.append(f"  KEEP {cls.category_label} / {cls.level}: {job.title} | {job.location}")
            for line in kept:
                print(line)
            for job in jobs[: args.limit]:
                cls = classify(job.title, search, in_country=job.in_country)
                print(f"  sample: {job.title} | {job.location} | uk={job.in_country} | "
                      f"{'kept' if cls.relevant else cls.reason} | {job.url}")
    return 0


def cmd_probe(_args) -> int:
    from .probe import main
    main()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tracker", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="check job boards and update everything")
    run.add_argument("--only", help="comma-separated company names to check (for testing)")
    run.add_argument("--no-notify", action="store_true", help="don't open issues or send alerts")
    run.add_argument("--dry-run", action="store_true", help="print results without saving")
    run.set_defaults(func=cmd_run)
    sub.add_parser("render", help="rebuild outputs from saved data").set_defaults(func=cmd_render)
    sub.add_parser("probe", help="detect job-board platforms").set_defaults(func=cmd_probe)
    diag = sub.add_parser("diagnose", help="show what each job board returns and why")
    diag.add_argument("--only", help="comma-separated company names")
    diag.add_argument("--limit", type=int, default=8, help="sample jobs to print per board")
    diag.set_defaults(func=cmd_diagnose)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(message)s", stream=sys.stdout)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
