"""Sends alerts about new roles: a GitHub issue, and optionally a phone push or an email."""
from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

import requests

from .render import LEVELS, TAGS, dashboard_url, repo_slug

log = logging.getLogger("tracker")
MAX_ISSUE_ROWS = 150


def worth_alerting(job: dict) -> bool:
    if "old_intake" in job.get("tags", []):
        return False
    return job.get("priority") or job.get("level") != "check"


def _line(job: dict) -> str:
    tags = [TAGS.get(t, t) for t in job.get("tags", [])]
    extra = f" _({', '.join(tags)})_" if tags else ""
    loc = f" · {job['location']}" if job.get("location") else ""
    return (f"- **{job['company']}** — [{job['title']}]({job['url']}){extra}  \n"
            f"  {job['category_label']} · {LEVELS.get(job['level'], '')}{loc}")


def issue_body(jobs: list[dict], intro: str) -> str:
    priority = [j for j in jobs if j.get("priority")]
    other = [j for j in jobs if not j.get("priority")]
    parts = [intro, ""]
    if priority:
        parts += ["### Regulatory, medical and clinical operations roles", ""]
        parts += [_line(j) for j in priority[:MAX_ISSUE_ROWS]]
        parts.append("")
    if other:
        parts += ["### Other roles", ""]
        parts += [_line(j) for j in other[:MAX_ISSUE_ROWS]]
        parts.append("")
    if len(jobs) > 2 * MAX_ISSUE_ROWS:
        parts.append("_List shortened; see the README for everything._\n")
    dash = dashboard_url()
    if dash:
        parts.append(f"[Open the dashboard]({dash}) to filter these and track your applications.")
    owner = os.environ.get("GITHUB_REPOSITORY_OWNER")
    if owner:
        parts.append(f"\ncc @{owner}")
    return "\n".join(parts)


def create_issue(title: str, body: str) -> dict | None:
    token, repo = os.environ.get("GITHUB_TOKEN"), repo_slug()
    if not token or not repo:
        log.info("No GITHUB_TOKEN; skipping GitHub issue")
        return None
    resp = requests.post(
        f"https://api.github.com/repos/{repo}/issues",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        json={"title": title, "body": body, "labels": ["new-openings"]},
        timeout=30,
    )
    if resp.status_code >= 300:
        log.warning("Could not create issue: %s %s", resp.status_code, resp.text[:300])
        return None
    return resp.json()


def push_ntfy(title: str, jobs: list[dict], click: str) -> None:
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        return
    server = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
    lines = [f"{j['company']}: {j['title']}" for j in jobs[:12]]
    if len(jobs) > 12:
        lines.append(f"…and {len(jobs) - 12} more")
    headers = {"Title": title.encode("utf-8"), "Tags": "pill"}
    if click:
        headers["Click"] = click
    try:
        requests.post(f"{server}/{topic}", data="\n".join(lines).encode("utf-8"),
                      headers=headers, timeout=20).raise_for_status()
    except requests.RequestException as exc:
        log.warning("ntfy push failed: %s", exc)


def send_email(title: str, jobs: list[dict], link: str) -> None:
    host, to = os.environ.get("SMTP_HOST"), os.environ.get("EMAIL_TO")
    if not host or not to:
        return
    user = os.environ.get("SMTP_USERNAME", "")
    msg = EmailMessage()
    msg["Subject"] = title
    msg["From"] = os.environ.get("EMAIL_FROM") or user
    msg["To"] = to
    body = [f"{j['company']} — {j['title']}\n  {j['category_label']} · "
            f"{LEVELS.get(j['level'], '')} · {j.get('location') or ''}\n  {j['url']}\n"
            for j in jobs]
    if link:
        body.append(f"\nAll roles: {link}")
    msg.set_content("\n".join(body))
    try:
        with smtplib.SMTP(host, int(os.environ.get("SMTP_PORT", "587")), timeout=30) as smtp:
            smtp.starttls()
            if user:
                smtp.login(user, os.environ.get("SMTP_PASSWORD", ""))
            smtp.send_message(msg)
    except (OSError, smtplib.SMTPException) as exc:
        log.warning("Email failed: %s", exc)


def announce(jobs: list[dict], title: str, intro: str) -> dict | None:
    jobs = sorted(jobs, key=lambda j: (not j.get("priority"), -int(j.get("score", 0))))
    issue = create_issue(title, issue_body(jobs, intro))
    click = (issue or {}).get("html_url") or dashboard_url()
    push_ntfy(title, jobs, click)
    send_email(title, jobs, click)
    return issue
