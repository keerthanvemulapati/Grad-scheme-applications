"""Shared pieces for job-board adapters."""
from __future__ import annotations

import datetime as dt
import re

from bs4 import BeautifulSoup

from ..classify import location_status
from ..config import Company, SearchConfig, SourceConfig
from ..http import PoliteSession
from ..models import RawJob


class SourceError(RuntimeError):
    """Raised when a job board can't be read."""


class Source:
    type = ""
    supports_enrich = False

    def __init__(self, company: Company, cfg: SourceConfig, search: SearchConfig,
                 session: PoliteSession | None = None):
        self.company = company
        self.cfg = cfg
        self.options = cfg.options
        self.search = search
        self.http = session or PoliteSession()
        self.scanned = 0
        self.note = ""
        self.complete = True
        self.uk_only = bool(self.options.get("uk_only"))

    def fetch(self) -> list[RawJob]:  # pragma: no cover - interface
        raise NotImplementedError

    def enrich(self, job: RawJob) -> RawJob:
        """Fetch the full advert. Adapters that list full adverts already skip this."""
        return job

    def where(self, text: str) -> bool | None:
        if self.uk_only:
            return True
        return location_status(text, self.search)

    def require(self, key: str) -> str:
        value = self.options.get(key)
        if not value:
            raise SourceError(f"'{key}' is missing for {self.company.name} ({self.type})")
        return str(value).rstrip("/")


def html_to_text(html: str) -> str:
    if not html:
        return ""
    return " ".join(BeautifulSoup(html, "html.parser").get_text(" ").split())


def iso_date(value) -> str | None:
    """Best-effort conversion of the many date formats job boards use."""
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        seconds = value / 1000 if value > 10_000_000_000 else value
        return dt.datetime.fromtimestamp(seconds, dt.timezone.utc).date().isoformat()
    text = str(value).strip()
    m = re.match(r"(\d{4}-\d{2}-\d{2})", text)
    if m:
        return m.group(1)
    for fmt in ("%d %b %Y", "%b %d, %Y", "%d/%m/%Y", "%B %d, %Y", "%d %B %Y"):
        try:
            return dt.datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def relative_posted(text: str | None, today: dt.date | None = None) -> str | None:
    """Turn Workday's 'Posted 3 Days Ago' into a date. '30+ Days Ago' is unknown."""
    if not text:
        return None
    today = today or dt.datetime.now(dt.timezone.utc).date()
    t = text.lower()
    if "today" in t:
        return today.isoformat()
    if "yesterday" in t:
        return (today - dt.timedelta(days=1)).isoformat()
    m = re.search(r"(\d+)\s*(\+)?\s*days?", t)
    if m and not m.group(2):
        return (today - dt.timedelta(days=int(m.group(1)))).isoformat()
    return None
