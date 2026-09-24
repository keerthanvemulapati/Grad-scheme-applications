"""Workday job boards (<tenant>.wdN.myworkdayjobs.com), used by most big pharma and CROs."""
from __future__ import annotations

import re
from urllib.parse import urlparse

from ..models import RawJob
from .base import Source, SourceError, html_to_text, relative_posted

PAGE_SIZE = 20
MAX_JOBS = 3000
FALLBACK_PAGES = 5
LOCALE_RE = re.compile(r"^[a-z]{2}(?:-[A-Z]{2})?$")
REQ_RE = re.compile(r"_([A-Za-z]{0,5}-?\d[\w-]*)$")


def find_country_facet(facets: list, countries: list[str]) -> tuple[str, list[str]] | None:
    """Find the facet that filters by country, and the ids of the wanted countries."""
    wanted = {c.strip().lower() for c in countries}
    best: tuple[int, str, list[str]] | None = None

    def walk(items) -> None:
        nonlocal best
        for facet in items or []:
            if not isinstance(facet, dict):
                continue
            param = facet.get("facetParameter")
            values = facet.get("values") or []
            if param and values:
                ids = [
                    v["id"] for v in values
                    if isinstance(v, dict) and v.get("id")
                    and (v.get("descriptor") or "").strip().lower() in wanted
                ]
                if ids:
                    score = 2 if "country" in param.lower() else 1
                    if best is None or score > best[0]:
                        best = (score, param, ids)
                walk(values)

    walk(facets)
    return (best[1], best[2]) if best else None


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

    def _page(self, text: str, facets: dict, offset: int) -> dict:
        body = {"appliedFacets": facets, "limit": PAGE_SIZE, "offset": offset, "searchText": text}
        return self.http.post(
            f"{self.api}/jobs", json=body,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        ).json()

    def fetch(self) -> list[RawJob]:
        first = self._page("", {}, 0)
        if "jobPostings" not in first:
            raise SourceError("Unexpected Workday response (no jobPostings)")
        jobs: dict[str, RawJob] = {}
        facet = find_country_facet(first.get("facets", []), self.search.countries)
        if facet:
            param, ids = facet
            self._collect("", {param: ids}, jobs, in_country=True)
            self.note = f"filtered by country ({param})"
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
        data = self.http.get(
            f"{self.api}{job.extra['path']}", headers={"Accept": "application/json"}
        ).json()
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
