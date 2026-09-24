"""Writes the README tables, the dashboard data file and the RSS feed."""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
from email.utils import format_datetime
from xml.sax.saxutils import escape

from .config import ROOT

README_PATH = ROOT / "README.md"
DASHBOARD_DATA = ROOT / "docs" / "data" / "jobs.json"
FEED_PATH = ROOT / "docs" / "feed.xml"
START, END = "<!-- TRACKER:START -->", "<!-- TRACKER:END -->"

LEVELS = {"graduate_scheme": "Graduate scheme", "entry_level": "Entry level",
          "check": "Check seniority"}
TAGS = {"register_interest": "register interest", "experience_required": "asks for experience",
        "graduate_friendly": "graduate-friendly", "location_unclear": "location unclear",
        "old_intake": "earlier intake"}
PRIORITY_ORDER = ["regulatory_affairs", "medical_affairs", "clinical_operations"]
NEW_DAYS = 7
PUBLIC_FIELDS = ("id", "company", "company_type", "title", "url", "location", "posted",
                 "category", "category_label", "priority", "level", "tags", "score",
                 "first_seen", "last_seen", "status", "closed_on", "baseline")


def repo_slug() -> str:
    slug = os.environ.get("GITHUB_REPOSITORY", "")
    if slug:
        return slug
    try:
        url = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True,
                             text=True, cwd=ROOT, check=False).stdout.strip()
    except OSError:
        return ""
    m = re.search(r"github\.com[:/]([^/]+/[^/.]+?)(?:\.git)?$", url)
    return m.group(1) if m else ""


def dashboard_url() -> str:
    slug = repo_slug()
    if "/" not in slug:
        return ""
    owner, repo = slug.split("/", 1)
    return f"https://{owner.lower()}.github.io/{repo}/"


def _cell(text: str, limit: int = 0) -> str:
    text = " ".join(str(text or "").split()).replace("|", "/")
    if limit and len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return text


def _date(value: str | None) -> str:
    if not value:
        return ""
    try:
        return dt.date.fromisoformat(value[:10]).strftime("%-d %b")
    except ValueError:
        return value


def _role(job: dict) -> str:
    title = _cell(job["title"], 90).replace("[", "(").replace("]", ")")
    tags = [TAGS.get(t, t) for t in job.get("tags", [])]
    suffix = f" <sub>{', '.join(tags)}</sub>" if tags else ""
    return f"[{title}]({job['url']}){suffix}"


def _table(jobs: list[dict], with_area: bool = False) -> str:
    if not jobs:
        return "_None right now._\n"
    head = "| Company | Role | " + ("Area | " if with_area else "") + "Level | Location | Found |"
    sep = "|---|---|" + ("---|" if with_area else "") + "---|---|---|"
    lines = [head, sep]
    for j in jobs:
        area = f"{_cell(j['category_label'])} | " if with_area else ""
        lines.append(f"| {_cell(j['company'])} | {_role(j)} | {area}{LEVELS.get(j['level'], '')} | "
                     f"{_cell(j.get('location'), 40)} | {_date(j.get('first_seen'))} |")
    return "\n".join(lines) + "\n"


def _age(job: dict) -> int:
    first = job.get("first_seen")
    return -dt.date.fromisoformat(first).toordinal() if first else 0


def _sort(jobs: list[dict]) -> list[dict]:
    """Best matches first, then newest first."""
    return sorted(jobs, key=lambda j: (-int(j.get("score", 0)), _age(j), j["company"], j["title"]))


def build_readme_section(state: dict, health: dict, watchlist: dict, now: dt.datetime) -> str:
    today = now.date()
    jobs = list(state["jobs"].values())
    open_jobs = [j for j in jobs if j.get("status") == "open"]
    current = [j for j in open_jobs if "old_intake" not in j.get("tags", [])]
    old_intake = [j for j in open_jobs if "old_intake" in j.get("tags", [])]
    closed = sorted([j for j in jobs if j.get("status") == "closed"],
                    key=lambda j: j.get("closed_on") or "", reverse=True)
    recent = [j for j in current if j.get("first_seen") and not j.get("baseline") and
              (today - dt.date.fromisoformat(j["first_seen"])).days < NEW_DAYS]
    recent.sort(key=lambda j: (j["first_seen"], j.get("score", 0)), reverse=True)

    companies = len({j["company"] for j in current})
    dash = dashboard_url()
    out = [START, ""]
    summary = (f"**Last refreshed:** {now.strftime('%-d %b %Y, %H:%M')} UTC · "
               f"**{len(current)} open roles** at {companies} companies")
    if dash:
        summary += f" · [Open the dashboard]({dash})"
    out += [summary, ""]

    # Counts grid
    cats = PRIORITY_ORDER + ["other"]
    labels = {"regulatory_affairs": "Regulatory Affairs", "medical_affairs": "Medical Affairs",
              "clinical_operations": "Clinical Operations", "other": "Other areas"}
    out += ["| | " + " | ".join(labels[c] for c in cats) + " |",
            "|---|" + "---|" * len(cats)]
    for level, label in LEVELS.items():
        row = []
        for c in cats:
            n = sum(1 for j in current if j["level"] == level and
                    (j["category"] == c if c != "other" else j["category"] not in PRIORITY_ORDER))
            row.append(str(n))
        out.append(f"| {label} | " + " | ".join(row) + " |")
    out.append("")

    out += [f"### New in the last {NEW_DAYS} days ({len(recent)})", ""]
    if not recent and all(j.get("baseline") for j in current):
        out += ["_Nothing yet. Everything below was already open when the tracker started; "
                "new postings will appear here._", ""]
    else:
        out.append(_table(recent, True))

    for key in PRIORITY_ORDER:
        group = _sort([j for j in current if j["category"] == key])
        label = labels[key]
        out += [f"### {label} ({len(group)})", "", _table(group)]

    others = _sort([j for j in current if j["category"] not in PRIORITY_ORDER])
    out += [f"### Other roles worth a look ({len(others)})", "",
            "<details><summary>Drug safety, clinical data, medical writing and other graduate "
            "schemes</summary>", "", _table(others, True), "</details>", ""]

    if old_intake or closed:
        out += ["### Earlier intakes and closed roles", "",
                f"<details><summary>{len(old_intake)} earlier-intake adverts still up, "
                f"{len(closed)} closed recently</summary>", ""]
        if old_intake:
            out += ["**Adverts naming an earlier intake year**", "", _table(_sort(old_intake), True)]
        if closed:
            out += ["**Closed recently**", "", "| Company | Role | Closed |", "|---|---|---|"]
            out += [f"| {_cell(j['company'])} | {_role(j)} | {_date(j.get('closed_on'))} |"
                    for j in closed[:40]]
            out.append("")
        out += ["</details>", ""]

    programmes = watchlist.get("programmes") or []
    if programmes:
        out += ["### Programmes to watch", "",
                "Schemes that open at set times of year or are advertised outside the job "
                "boards above. Check these by hand.", "",
                "| Company | Programme | Area | Notes |", "|---|---|---|---|"]
        for p in programmes:
            out.append(f"| {_cell(p.get('company'))} | [{_cell(p.get('programme'))}]({p.get('url')})"
                       f" | {_cell(p.get('area'))} | {_cell(p.get('notes'))} |")
        out.append("")
    links = watchlist.get("links") or []
    if links:
        out += ["**Other places to look:** " + " · ".join(
            f"[{_cell(l['name'])}]({l['url']})" for l in links), ""]

    ok = sum(1 for h in health.values() if h.get("ok"))
    out += ["### Job board status", "",
            f"<details><summary>{ok} of {len(health)} job boards read successfully on the last "
            "run</summary>", "",
            "| Company | Board | Status | Jobs read | Matches | Notes |", "|---|---|---|---|---|---|"]
    for key, h in sorted(health.items(), key=lambda kv: (kv[1].get("ok", False), kv[0])):
        status = "OK" if h.get("ok") else f"Failing ({h.get('failures_in_a_row', 1)}x)"
        note = h.get("error") or h.get("note") or ""
        out.append(f"| {_cell(h.get('company'))} | {h.get('type')} | {status} | "
                   f"{h.get('scanned', 0)} | {h.get('matches', 0)} | {_cell(note, 80)} |")
    out += ["", "</details>", "", END]
    return "\n".join(out)


def write_readme(section: str) -> None:
    text = README_PATH.read_text() if README_PATH.exists() else f"{START}\n{END}\n"
    if START not in text or END not in text:
        text = text.rstrip() + f"\n\n{START}\n{END}\n"
    before = text.split(START)[0]
    after = text.split(END, 1)[1]
    README_PATH.write_text(before + section + after)


def public_job(job: dict) -> dict:
    return {k: job.get(k) for k in PUBLIC_FIELDS}


def write_dashboard_data(state: dict, health: dict, watchlist: dict, now: dt.datetime) -> None:
    jobs = [public_job(j) for j in state["jobs"].values()]
    jobs.sort(key=lambda j: (j.get("first_seen") or "", j.get("score") or 0), reverse=True)
    data = {
        "generated": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repo": repo_slug(),
        "jobs": jobs,
        "watchlist": watchlist,
        "health": {k: {kk: v.get(kk) for kk in ("company", "type", "ok", "scanned", "matches",
                                                "error", "note", "last_ok")}
                   for k, v in health.items()},
    }
    DASHBOARD_DATA.parent.mkdir(parents=True, exist_ok=True)
    DASHBOARD_DATA.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")


def write_feed(state: dict, now: dt.datetime) -> None:
    jobs = [j for j in state["jobs"].values()
            if j.get("status") == "open" and "old_intake" not in j.get("tags", [])
            and not j.get("baseline")]
    jobs.sort(key=lambda j: (j.get("first_seen") or "", j.get("score", 0)), reverse=True)
    link = dashboard_url() or f"https://github.com/{repo_slug()}"
    items = []
    for j in jobs[:100]:
        first = dt.datetime.fromisoformat(j["first_seen"]).replace(tzinfo=dt.timezone.utc)
        desc = f"{j['category_label']} · {LEVELS.get(j['level'], '')} · {j.get('location') or ''}"
        items.append(
            "  <item>\n"
            f"   <title>{escape(j['company'] + ' — ' + j['title'])}</title>\n"
            f"   <link>{escape(j['url'])}</link>\n"
            f"   <guid isPermaLink=\"false\">{escape(j['id'])}</guid>\n"
            f"   <pubDate>{format_datetime(first)}</pubDate>\n"
            f"   <description>{escape(desc)}</description>\n"
            "  </item>")
    xml = ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<rss version=\"2.0\">\n <channel>\n"
           "  <title>Pharma graduate scheme tracker</title>\n"
           f"  <link>{escape(link)}</link>\n"
           "  <description>New graduate and entry-level roles in regulatory affairs, medical "
           "affairs and clinical operations.</description>\n"
           f"  <lastBuildDate>{format_datetime(now)}</lastBuildDate>\n"
           + "\n".join(items) + "\n </channel>\n</rss>\n")
    FEED_PATH.parent.mkdir(parents=True, exist_ok=True)
    FEED_PATH.write_text(xml)


def render_all(state: dict, health: dict, watchlist: dict, now: dt.datetime) -> None:
    write_readme(build_readme_section(state, health, watchlist, now))
    write_dashboard_data(state, health, watchlist, now)
    write_feed(state, now)
