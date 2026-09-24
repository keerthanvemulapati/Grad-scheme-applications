"""Keeps the list of tracked roles between runs and works out what changed."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from .config import ROOT
from .models import SourceResult

STATE_PATH = ROOT / "data" / "jobs.json"
HEALTH_PATH = ROOT / "data" / "sources.json"
CLOSE_AFTER_MISSES = 2       # runs a role must be missing before it counts as closed
KEEP_CLOSED_DAYS = 60        # how long closed roles stay in the data
PARTIAL_EXPIRY_DAYS = 30     # boards that only show their newest jobs: close after this long unseen
STICKY_FIELDS = ("posted", "location", "facts", "in_country")


def empty_state() -> dict:
    return {"meta": {"version": 1, "sources_seen_ok": [], "snapshot_issue": None}, "jobs": {}}


def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False, sort_keys=True) + "\n")


def merge(state: dict, results: list[SourceResult], today: dt.date,
          configured_keys: set[str]) -> dict:
    """Fold one run's results into the saved state.

    Returns {"new": [...], "closed": [...], "reopened": [...], "silent": [...]}.
    Roles from a board that has never been read successfully before are added
    silently, so adding a company doesn't flood you with alerts.
    """
    jobs: dict = state["jobs"]
    meta = state["meta"]
    today_s = today.isoformat()
    ok_keys = {r.source_key for r in results if r.ok}
    complete_keys = {r.source_key for r in results if r.ok and r.complete}
    known_ok = set(meta.get("sources_seen_ok", []))
    changes: dict[str, list] = {"new": [], "closed": [], "reopened": [], "silent": []}
    seen: set[str] = set()

    for result in results:
        if not result.ok:
            continue
        first_time = result.source_key not in known_ok
        for rec in result.jobs:
            jid = rec["id"]
            if jid in seen:
                continue
            seen.add(jid)
            old = jobs.get(jid)
            if old is None:
                rec.update(first_seen=today_s, last_seen=today_s, status="open",
                           closed_on=None, missed=0)
                jobs[jid] = rec
                changes["silent" if first_time else "new"].append(rec)
                continue
            was_closed = old.get("status") == "closed"
            for key, value in rec.items():
                if key in STICKY_FIELDS and not value and old.get(key):
                    continue
                old[key] = value
            old.update(last_seen=today_s, status="open", closed_on=None, missed=0)
            if was_closed:
                old["reopened_on"] = today_s
                changes["reopened"].append(old)

    for jid in list(jobs):
        job = jobs[jid]
        if job.get("source_key") not in configured_keys:
            del jobs[jid]  # company or board removed from the config
            continue
        key = job.get("source_key")
        if job.get("status") == "open" and jid not in seen and key in ok_keys:
            if key in complete_keys:
                job["missed"] = int(job.get("missed", 0)) + 1
                gone = job["missed"] >= CLOSE_AFTER_MISSES
            else:
                last = dt.date.fromisoformat(job.get("last_seen") or today_s)
                gone = (today - last).days > PARTIAL_EXPIRY_DAYS
            if gone:
                job["status"] = "closed"
                job["closed_on"] = today_s
                changes["closed"].append(job)
        if job.get("status") == "closed" and job.get("closed_on"):
            closed = dt.date.fromisoformat(job["closed_on"])
            if (today - closed).days > KEEP_CLOSED_DAYS:
                del jobs[jid]

    meta["sources_seen_ok"] = sorted(known_ok | ok_keys)
    return changes


def update_health(health: dict, results: list[SourceResult], today: dt.date,
                  configured_keys: set[str]) -> dict:
    today_s = today.isoformat()
    for r in results:
        prev = health.get(r.source_key, {})
        entry = {
            "company": r.company,
            "type": r.source_type,
            "ok": r.ok,
            "scanned": r.scanned if r.ok else prev.get("scanned", 0),
            "matches": len(r.jobs) if r.ok else prev.get("matches", 0),
            "note": r.note,
            "error": r.error,
            "last_ok": today_s if r.ok else prev.get("last_ok"),
            "failures_in_a_row": 0 if r.ok else int(prev.get("failures_in_a_row", 0)) + 1,
        }
        health[r.source_key] = entry
    for key in list(health):
        if key not in configured_keys:
            del health[key]
    return health
