"""Workday job boards (<tenant>.wdN.myworkdayjobs.com), used by most big pharma and CROs."""
from __future__ import annotations

import re
from urllib.parse import urlparse

import requests

from ..classify import location_status
from ..models import RawJob
from .base import Source, SourceError, html_to_text, relative_posted

PAGE_SIZE = 20
MAX_JOBS = 3000
FALLBACK_PAGES = 5
LOCALE_RE = re.compile(r"^[a-z]{2}(?:-[A-Z]{2})?$")
REQ_RE = re.compile(r"_([A-Za-z]{0,5}-?\d[\w-]*)$")
JSON_HEADERS = {"Accept": "application/json", "Content-Type": "application/json",
                "Accept-Language": "en-US,en;q=0.9"}


def _norm_country(text: str) -> str:
    return re.sub(r"\s*\([^)]*\)\s*$", "", (text or "").strip().lower())


def find_location_facet(facets: list, search) -> tuple[str, list[str], str] | None:
    """Work out how to ask a Workday board for jobs in the target countries.

    Boards differ: some have a country facet, some a location hierarchy, and some
    only list individual office locations. Returns (facet parameter, ids, kind).
    """
    wanted = {c.strip().lower() for c in search.countries}
    best: tuple[int, str, list[str], str] | None = None

    def consider(score: int, param: str, ids: list[str], kind: str) -> None:
        nonlocal best
        if ids and (best is None or score > best[0]):
            best = (score, param, ids, kind)

    def walk(items) -> None:
        for facet in items or []:
            if not isinstance(facet, dict):
                continue
            param = facet.get("facetParameter")
            values = [v for v in facet.get("values") or [] if isinstance(v, dict)]
            if param and values:
                exact = [v["id"] for v in values
                         if v.get("id") and _norm_country(v.get("descriptor")) in wanted]
                lowered = param.lower()
                if "country" in lowered:
                    consider(3, param, exact, "country")
                elif "hierarchy" in lowered:
                    consider(2, param, exact, "region")
                elif lowered == "locations":
                    matched = [v["id"] for v in values if v.get("id")
                               and location_status(v.get("descriptor") or "", search) is True]
                    consider(1, param, matched, f"{len(matched)} offices")
                walk(values)

    walk(facets)
    return (best[1], best[2], best[3]) if best else None


class WorkdaySource(Source):
    type = "workday"
    supports_enrich = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        parsed = urlparse(self.require("url"))
        if "myworkdayjobs.com" not in parsed.netloc:
            raise SourceError(f"Not a Workday URL: {self.options['url']}")
        parts = [p for p in parsed.path.split("/") if p]
        if parts and LOCALE_RE.match(parts[0]):
            parts = parts[1:]
        if not parts:
            raise SourceError(f"Workday URL has no site name: {self.options['url']}")
        self.host = parsed.netloc
        self.tenant = self.host.split(".")[0]
        self.site = parts[0]
        self.api = f"https://{self.host}/wday/cxs/{self.tenant}/{self.site}"
        self.public = f"https://{self.host}/en-US/{self.site}"
        self._csrf: str | None = None

    def _page(self, text: str, facets: dict, offset: int) -> dict:
        body = {"appliedFacets": facets, "limit": PAGE_SIZE, "offset": offset, "searchText": text}
        try:
            return self.http.post(f"{self.api}/jobs", json=body, headers=self._headers()).json()
        except requests.HTTPError as exc:
            if exc.response is None or exc.response.status_code != 422 or self._csrf is not None:
                raise
        # Some boards want the session cookie and CSRF token their own page sets.
        self.http.get(self.public, headers={"Accept": "text/html"})
        self._csrf = self.http.session.cookies.get("CALYPSO_CSRF_TOKEN") or ""
        return self.http.post(f"{self.api}/jobs", json=body, headers=self._headers()).json()

    def _headers(self) -> dict:
        headers = dict(JSON_HEADERS, Origin=f"https://{self.host}", Referer=self.public)
        if self._csrf:
            headers["X-CALYPSO-CSRF-TOKEN"] = self._csrf
        return headers

    def fetch(self) -> list[RawJob]:
        first = self._page("", {}, 0)
        if "jobPostings" not in first:
            raise SourceError("Unexpected Workday response (no jobPostings)")
        jobs: dict[str, RawJob] = {}
        facet = find_location_facet(first.get("facets", []), self.search)
        if facet:
            param, ids, kind = facet
            self._collect("", {param: ids}, jobs, in_country=True)
            self.note = f"filtered by location ({kind})"
        else:
            for query in self.search.fallback_queries:
                self._collect(query, {}, jobs, in_country=None, max_pages=FALLBACK_PAGES)
            self.note = "keyword search (board has no country filter)"
        self.scanned = len(jobs)
        return list(jobs.values())

    def _collect(self, text, facets, jobs, in_country, max_pages=None) -> None:
        offset, total, pages = 0, None, 0
        while True:
            data = self._page(text, facets, offset)
            if total is None:
                total = int(data.get("total") or 0)
            postings = data.get("jobPostings") or []
            if not postings:
                break
            for posting in postings:
                job = self._to_job(posting, in_country)
                if job:
                    jobs.setdefault(job.source_id, job)
            offset += len(postings)
            pages += 1
            if offset >= total or offset >= MAX_JOBS or (max_pages and pages >= max_pages):
                break

    def _to_job(self, posting: dict, in_country: bool | None) -> RawJob | None:
        path = posting.get("externalPath") or ""
        title = (posting.get("title") or "").strip()
        if not path or not title:
            return None
        last = path.rstrip("/").rsplit("/", 1)[-1]
        m = REQ_RE.search(last)
        source_id = m.group(1) if m else last
        location = posting.get("locationsText") or ""
        if in_country is None:
            in_country = self.where(location)
        return RawJob(
            source_id=source_id,
            title=title,
            url=f"{self.public}{path}",
            location=location,
            in_country=in_country,
            posted=relative_posted(posting.get("postedOn")),
            extra={"path": path},
        )

    def enrich(self, job: RawJob) -> RawJob:
        data = self.http.get(f"{self.api}{job.extra['path']}", headers=self._headers()).json()
        info = data.get("jobPostingInfo") or {}
        locations = [info.get("location") or ""] + list(info.get("additionalLocations") or [])
        loc_text = "; ".join(dict.fromkeys(l for l in locations if l))
        country = (info.get("country") or {}).get("descriptor") or ""
        if loc_text:
            job.location = loc_text
        if job.in_country is not True:
            job.in_country = self.where(f"{loc_text}; {country}")
        job.posted = (info.get("startDate") or job.posted or None)
        if job.posted:
            job.posted = job.posted[:10]
        job.description = html_to_text(info.get("jobDescription") or "")
        job.enriched = True
        return job
