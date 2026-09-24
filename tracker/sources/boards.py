"""Adapters for the other job-board platforms pharma companies and CROs use."""
from __future__ import annotations

import html as htmllib
import json
import re
from urllib.parse import quote, urljoin, urlparse

from bs4 import BeautifulSoup

from ..models import RawJob
from .base import Source, SourceError, html_to_text, iso_date

MAX_PAGES = 40


class EightfoldSource(Source):
    """Eightfold career sites (e.g. talent.bayer.com)."""

    type = "eightfold"
    supports_enrich = True

    def fetch(self) -> list[RawJob]:
        base = self.require("url")
        domain = self.require("domain")
        jobs: dict[str, RawJob] = {}
        for country in self.search.countries:
            start = 0
            for _ in range(MAX_PAGES):
                data = self.http.get(
                    f"{base}/api/apply/v2/jobs",
                    params={"domain": domain, "start": start, "num": 50,
                            "location": country, "sort_by": "timestamp"},
                    headers={"Accept": "application/json"},
                ).json()
                positions = data.get("positions")
                if positions is None:
                    raise SourceError("Unexpected Eightfold response (no positions)")
                for p in positions:
                    locs = p.get("locations") or [p.get("location") or ""]
                    loc = "; ".join(l for l in locs if l)
                    jid = str(p.get("id"))
                    jobs.setdefault(jid, RawJob(
                        source_id=jid,
                        title=(p.get("name") or "").strip(),
                        url=p.get("canonicalPositionUrl") or f"{base}/careers?pid={jid}&domain={domain}",
                        location=loc,
                        in_country=self.where(loc),
                        posted=iso_date(p.get("t_create")),
                        extra={"id": jid},
                    ))
                start += len(positions)
                if not positions or start >= int(data.get("count") or 0):
                    break
        self.scanned = len(jobs)
        return list(jobs.values())

    def enrich(self, job: RawJob) -> RawJob:
        base, domain = self.require("url"), self.require("domain")
        data = self.http.get(
            f"{base}/api/apply/v2/jobs/{job.extra['id']}", params={"domain": domain},
            headers={"Accept": "application/json"},
        ).json()
        job.description = html_to_text(data.get("job_description") or "")
        job.enriched = True
        return job


class JibeSource(Source):
    """Jibe / iCIMS career sites that expose /api/jobs (e.g. careers.medpace.com)."""

    type = "jibe"

    def fetch(self) -> list[RawJob]:
        base = self.require("url")
        jobs: dict[str, RawJob] = {}
        total = None
        for page in range(1, MAX_PAGES + 1):
            data = self.http.get(
                f"{base}/api/jobs",
                params={"page": page, "limit": 100, "sortBy": "posted_date", "descending": "true",
                        "internal": "false"},
                headers={"Accept": "application/json"},
            ).json()
            if "jobs" not in data:
                raise SourceError("Unexpected Jibe response (no jobs)")
            total = total if total is not None else int(data.get("totalCount") or 0)
            for item in data["jobs"]:
                d = item.get("data", item)
                slug = str(d.get("slug") or d.get("req_id") or "")
                if not slug:
                    continue
                loc = d.get("full_location") or ", ".join(
                    x for x in (d.get("city"), d.get("state"), d.get("country")) if x)
                code = (d.get("country_code") or "").upper()
                in_country = True if code in {"GB", "UK"} else self.where(f"{loc}; {d.get('country') or ''}")
                jobs.setdefault(slug, RawJob(
                    source_id=slug,
                    title=(d.get("title") or "").strip(),
                    url=f"{base}/jobs/{slug}?lang=en-us",
                    location=loc,
                    in_country=in_country,
                    posted=iso_date(d.get("posted_date") or d.get("create_date")),
                    description=html_to_text(d.get("description") or ""),
                    enriched=True,
                ))
            if not data["jobs"] or len(jobs) >= total:
                break
        self.scanned = len(jobs)
        return list(jobs.values())


class PhenomSource(Source):
    """Phenom People career sites (careers.<company>.com/<region>/<lang>)."""

    type = "phenom"
    PAGE = 10
    PAGES_PER_QUERY = 5

    @staticmethod
    def _ddo(html: str) -> dict:
        idx = html.find("phApp.ddo")
        if idx < 0:
            raise SourceError("Page is not a Phenom site (phApp.ddo not found)")
        start = html.find("{", idx)
        obj, _ = json.JSONDecoder().raw_decode(html[start:])
        return obj

    def fetch(self) -> list[RawJob]:
        base = self.require("url")
        jobs: dict[str, RawJob] = {}
        for query in self.search.fallback_queries:
            for page in range(self.PAGES_PER_QUERY):
                html = self.http.get(
                    f"{base}/search-results",
                    params={"keywords": query, "from": page * self.PAGE, "s": 1},
                ).text
                search = self._ddo(html).get("eagerLoadRefineSearch") or {}
                found = ((search.get("data") or {}).get("jobs")) or []
                for j in found:
                    jid = str(j.get("jobId") or j.get("reqId") or j.get("jobSeqNo") or "")
                    if not jid:
                        continue
                    locs = j.get("multi_location") or [j.get("location") or ""]
                    loc = "; ".join(l for l in locs if l) or ", ".join(
                        x for x in (j.get("city"), j.get("country")) if x)
                    jobs.setdefault(jid, RawJob(
                        source_id=jid,
                        title=(j.get("title") or "").strip(),
                        url=f"{base}/job/{quote(jid)}",
                        location=loc,
                        in_country=self.where(f"{loc}; {j.get('country') or ''}"),
                        posted=iso_date(j.get("postedDate") or j.get("dateCreated")),
                        description=j.get("descriptionTeaser") or "",
                    ))
                total = int(search.get("totalHits") or 0)
                if len(found) < self.PAGE or (page + 1) * self.PAGE >= total:
                    break
        self.scanned = len(jobs)
        return list(jobs.values())


class SuccessFactorsSource(Source):
    """SAP SuccessFactors career sites (jobs.<company>.com/search/)."""

    type = "successfactors"
    PAGE = 25

    def fetch(self) -> list[RawJob]:
        base = self.require("url")
        jobs: dict[str, RawJob] = {}
        for country in self.search.countries:
            for page in range(MAX_PAGES):
                html = self.http.get(
                    f"{base}/search/",
                    params={"q": "", "locationsearch": country, "startrow": page * self.PAGE},
                ).text
                soup = BeautifulSoup(html, "html.parser")
                rows = soup.select("tr.data-row")
                if page == 0 and not rows and not soup.select("#searchresults, .searchResults"):
                    raise SourceError("Page is not a SuccessFactors job search")
                added = 0
                for row in rows:
                    link = row.select_one("a.jobTitle-link")
                    if not link or not link.get("href"):
                        continue
                    href = urljoin(base + "/", link["href"])
                    loc_el = row.select_one("span.jobLocation")
                    date_el = row.select_one("span.jobDate")
                    loc = " ".join(loc_el.get_text(" ").split()) if loc_el else country
                    if href not in jobs:
                        added += 1
                        m = re.search(r"/(\d+)/?$", href)
                        jobs[href] = RawJob(
                            source_id=m.group(1) if m else href,
                            title=" ".join(link.get_text(" ").split()),
                            url=href,
                            location=loc,
                            in_country=self.where(f"{loc}; {country}"),
                            posted=iso_date(date_el.get_text(strip=True)) if date_el else None,
                        )
                if len(rows) == 0 or added == 0:
                    break
        self.scanned = len(jobs)
        return list(jobs.values())


class GreenhouseSource(Source):
    type = "greenhouse"

    def fetch(self) -> list[RawJob]:
        board = self.require("board")
        data = self.http.get(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs",
                             params={"content": "true"}).json()
        out = []
        for j in data.get("jobs", []):
            loc = (j.get("location") or {}).get("name") or ""
            out.append(RawJob(
                source_id=str(j["id"]),
                title=(j.get("title") or "").strip(),
                url=j.get("absolute_url") or "",
                location=loc,
                in_country=self.where(loc),
                posted=iso_date(j.get("first_published") or j.get("updated_at")),
                description=html_to_text(htmllib.unescape(j.get("content") or "")),
                enriched=True,
            ))
        self.scanned = len(out)
        return out


class LeverSource(Source):
    type = "lever"

    def fetch(self) -> list[RawJob]:
        company = self.require("company")
        data = self.http.get(f"https://api.lever.co/v0/postings/{company}",
                             params={"mode": "json"}).json()
        out = []
        for j in data:
            loc = ((j.get("categories") or {}).get("location")) or ""
            out.append(RawJob(
                source_id=str(j["id"]),
                title=(j.get("text") or "").strip(),
                url=j.get("hostedUrl") or "",
                location=loc,
                in_country=self.where(loc),
                posted=iso_date(j.get("createdAt")),
                description=j.get("descriptionPlain") or "",
                enriched=True,
            ))
        self.scanned = len(out)
        return out


class SmartRecruitersSource(Source):
    type = "smartrecruiters"

    def fetch(self) -> list[RawJob]:
        company = self.require("company")
        out: dict[str, RawJob] = {}
        offset = 0
        for _ in range(MAX_PAGES):
            data = self.http.get(
                f"https://api.smartrecruiters.com/v1/companies/{company}/postings",
                params={"limit": 100, "offset": offset},
            ).json()
            content = data.get("content") or []
            for j in content:
                loc_d = j.get("location") or {}
                loc = loc_d.get("fullLocation") or ", ".join(
                    x for x in (loc_d.get("city"), loc_d.get("country")) if x)
                code = (loc_d.get("country") or "").lower()
                jid = str(j["id"])
                out.setdefault(jid, RawJob(
                    source_id=jid,
                    title=(j.get("name") or "").strip(),
                    url=f"https://jobs.smartrecruiters.com/{company}/{jid}",
                    location=loc,
                    in_country=True if code == "gb" else self.where(loc),
                    posted=iso_date(j.get("releasedDate")),
                ))
            offset += len(content)
            if not content or offset >= int(data.get("totalFound") or 0):
                break
        self.scanned = len(out)
        return list(out.values())


class PinpointSource(Source):
    """Pinpoint ATS boards (<company>.pinpointhq.com)."""

    type = "pinpoint"

    def fetch(self) -> list[RawJob]:
        base = self.require("url")
        resp = self.http.get(f"{base}/postings.json", headers={"Accept": "application/json"})
        payload = resp.json()
        items = payload.get("data", payload) if isinstance(payload, dict) else payload
        out = []
        for j in items or []:
            attrs = j.get("attributes", j)
            loc_d = attrs.get("location")
            if isinstance(loc_d, dict):
                loc = loc_d.get("name") or ", ".join(
                    x for x in (loc_d.get("city"), loc_d.get("province")) if x)
            else:
                loc = str(loc_d or "")
            jid = str(j.get("id") or attrs.get("id"))
            url = attrs.get("url") or (urljoin(base + "/", attrs["path"]) if attrs.get("path")
                                       else f"{base}/postings/{jid}")
            out.append(RawJob(
                source_id=jid,
                title=(attrs.get("title") or "").strip(),
                url=url,
                location=loc or "",
                in_country=self.where(loc or ""),
                posted=iso_date(attrs.get("published_at") or attrs.get("created_at")),
                description=html_to_text(attrs.get("description") or ""),
                enriched=bool(attrs.get("description")),
            ))
        self.scanned = len(out)
        return out


GENERIC_LINK_TEXT = re.compile(
    r"^(?:careers?|jobs?|vacancies|apply(?: now| here| online)?|read more|learn more|find out more|"
    r"more|details|view(?: all)?(?: jobs| vacancies| roles| details| job| role| more)?|see (?:all|more)|"
    r"search(?: jobs)?|home|contact(?: us)?|about(?: us)?|privacy.*|cookies?.*|terms.*|login|log in|"
    r"sign in|register|next|previous|back|click here|here|current vacancies|job opportunities|"
    r"open positions|our people|meet the team|linkedin|twitter|facebook|instagram|youtube)$",
    re.IGNORECASE,
)
JOB_HREF = re.compile(r"job|vacanc|position|opening|role|recruit|posting|opportunit|career|apply",
                      re.IGNORECASE)
SKIP_HREF = re.compile(r"^(?:mailto:|tel:|javascript:|#)|linkedin\.com|facebook\.com|twitter\.com|"
                       r"x\.com/|instagram\.com|youtube\.com|glassdoor|indeed\.", re.IGNORECASE)


class PageWatchSource(Source):
    """Reads job links straight off a careers page. For small sites with no job-board API."""

    type = "pagewatch"

    def fetch(self) -> list[RawJob]:
        url = self.require("url")
        pattern = self.options.get("link_pattern")
        link_re = re.compile(pattern, re.IGNORECASE) if pattern else JOB_HREF
        default_loc = self.options.get("default_location", "")
        html = self.http.get(url).text
        soup = BeautifulSoup(html, "html.parser")
        page = urlparse(url)
        out: dict[str, RawJob] = {}
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if SKIP_HREF.search(href):
                continue
            full = urljoin(url, href)
            parsed = urlparse(full)
            if parsed.path.rstrip("/") == page.path.rstrip("/") and parsed.netloc == page.netloc:
                continue
            text = " ".join(a.get_text(" ").split())
            if not (4 <= len(text) <= 140) or GENERIC_LINK_TEXT.match(text):
                continue
            if not link_re.search(parsed.path + "?" + parsed.query):
                continue
            container = a.find_parent(["li", "article", "tr", "div"]) or a
            context = " ".join(container.get_text(" ").split())[:400]
            in_country = True if self.uk_only else self.where(f"{text}; {context}")
            out.setdefault(full, RawJob(
                source_id=full,
                title=text,
                url=full,
                location=default_loc or ("UK" if in_country else ""),
                in_country=in_country,
            ))
        self.scanned = len(out)
        if not out:
            self.note = "no job links found on page"
        return list(out.values())
