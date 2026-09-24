"""Adapters for the other job-board platforms pharma companies and CROs use."""
from __future__ import annotations

import html as htmllib
import json
import re
from urllib.parse import quote, urljoin, urlparse

import requests
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
        locations = self.options.get("locations")
        if locations:  # searching by city is complete for those cities
            for loc in locations:
                self._scan(base, domain, jobs, loc)
            self.complete = True
        else:
            self._scan(base, domain, jobs, None)
        self.scanned = len(jobs)
        return [j for j in jobs.values() if j.in_country is not False]

    def _scan(self, base: str, domain: str, jobs: dict, location: str | None) -> None:
        start = 0
        data: dict = {}
        for _ in range(MAX_PAGES):
            params = {"domain": domain, "start": start, "num": 100, "sort_by": "timestamp"}
            if location:
                params["location"] = location
            data = self.http.get(
                f"{base}/api/apply/v2/jobs", params=params, headers={"Accept": "application/json"},
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
        if not location:
            self.complete = start >= int(data.get("count") or 0)
            if not self.complete:
                self.note = f"newest {len(jobs)} of {data.get('count')} jobs"

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
                params={"page": page, "limit": 100, "lang": "en-us", "sortBy": "relevance",
                        "descending": "false", "internal": "false",
                        "location": self.options.get("location", self.search.countries[0])},
                # Jibe only returns jobs in the language it's asked for, so ask in US English.
                headers={"Accept": "application/json", "Accept-Language": "en-US,en;q=0.9"},
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
                country = d.get("country") or ""
                if code in {"GB", "UK"} or country in self.search.countries:
                    in_country = True
                else:
                    in_country = self.where(f"{loc}; {country}")
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
        if not jobs:
            raise SourceError("The Jibe jobs API returned no jobs")
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
        try:
            jobs = self._fetch_api()
            self.note = "search API filtered by country"
            return jobs
        except (SourceError, ValueError, KeyError, requests.RequestException) as exc:
            self.note = f"page data (search API unavailable: {type(exc).__name__})"
        return self._fetch_pages()

    def _job(self, base: str, j: dict) -> RawJob | None:
        jid = str(j.get("jobId") or j.get("reqId") or j.get("jobSeqNo") or "")
        if not jid:
            return None
        locs = j.get("multi_location") or [j.get("location") or ""]
        loc = "; ".join(l for l in locs if l) or ", ".join(
            x for x in (j.get("city"), j.get("country")) if x)
        country = j.get("country") or ""
        return RawJob(
            source_id=jid,
            title=(j.get("title") or "").strip(),
            url=f"{base}/job/{quote(jid)}",
            location=loc,
            in_country=True if country in self.search.countries else self.where(f"{loc}; {country}"),
            posted=iso_date(j.get("postedDate") or j.get("dateCreated")),
            description=j.get("descriptionTeaser") or "",
        )

    def _fetch_api(self) -> list[RawJob]:
        base = self.require("url")
        parsed = urlparse(base)
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) < 2:
            raise SourceError("URL should end in /<region>/<language>")
        region, lang = parts[-2], parts[-1]
        page = self.http.get(f"{base}/search-results", headers={"Accept": "text/html"}).text
        token = re.search(r'"csrfToken"\s*:\s*"([^"]+)"', page)
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if token:
            headers["x-csrf-token"] = token.group(1)
        jobs: dict[str, RawJob] = {}
        size, offset, total = 50, 0, None
        for _ in range(MAX_PAGES):
            payload = {"lang": f"{lang}_{region}", "deviceType": "desktop", "country": region,
                       "pageName": "search-results", "ddoKey": "refineSearch", "sortBy": "",
                       "subsearch": "", "from": offset, "jobs": True, "counts": True,
                       "all_fields": ["category", "country", "state", "city"], "size": size,
                       "clearAll": False, "jdsource": "facets", "isSliderEnable": False,
                       "keywords": "", "global": True, "siteType": "external",
                       "selected_fields": {"country": list(self.search.countries)}}
            data = self.http.post(f"{parsed.scheme}://{parsed.netloc}/widgets", json=payload,
                                  headers=headers).json()
            search = data["refineSearch"]
            found = (search.get("data") or {}).get("jobs") or []
            total = int(search.get("totalHits") or 0) if total is None else total
            for j in found:
                job = self._job(base, j)
                if job:
                    jobs.setdefault(job.source_id, job)
            offset += len(found)
            if not found or offset >= total:
                break
        self.scanned = len(jobs)
        return [j for j in jobs.values() if j.in_country is not False]

    def _fetch_pages(self) -> list[RawJob]:
        base = self.require("url")
        jobs: dict[str, RawJob] = {}
        queries = self.options.get("keywords") or self.search.fallback_queries
        self.complete = False
        for query in queries:
            for page in range(self.PAGES_PER_QUERY):
                html = self.http.get(
                    f"{base}/search-results",
                    params={"keywords": query, "from": page * self.PAGE, "s": 1},
                ).text
                search = self._ddo(html).get("eagerLoadRefineSearch") or {}
                found = ((search.get("data") or {}).get("jobs")) or []
                for j in found:
                    job = self._job(base, j)
                    if job:
                        jobs.setdefault(job.source_id, job)
                total = int(search.get("totalHits") or 0)
                if len(found) < self.PAGE or (page + 1) * self.PAGE >= total:
                    break
        self.scanned = len(jobs)
        return list(jobs.values())


class SuccessFactorsSource(Source):
    """SAP SuccessFactors career sites with a /search/ page (jobs.<company>.com)."""

    type = "successfactors"
    PAGE = 25

    def _page(self, base: str, params: dict, startrow: int) -> list[RawJob]:
        html = self.http.get(f"{base}/search/", params=dict(params, startrow=startrow),
                             headers={"Accept": "text/html"}).text
        soup = BeautifulSoup(html, "html.parser")
        out: dict[str, RawJob] = {}
        for link in soup.select("a.jobTitle-link"):
            href = link.get("href")
            if not href:
                continue
            full = urljoin(base + "/", href)
            box = link.find_parent(["tr", "li"]) or link.find_parent(
                class_=re.compile(r"job-tile|data-row|job-row")) or link.parent
            loc_el = box.select_one(".jobLocation, [class*=location], [class*=Location]") if box else None
            date_el = box.select_one(".jobDate, [class*=date]") if box else None
            loc = " ".join(loc_el.get_text(" ").split()) if loc_el else ""
            m = re.search(r"/(\d+)/?$", full)
            out.setdefault(full, RawJob(
                source_id=m.group(1) if m else full,
                title=" ".join(link.get_text(" ").split()),
                url=full,
                location=loc,
                in_country=self.where(loc) if loc else None,
                posted=iso_date(" ".join(date_el.get_text(" ").split())) if date_el else None,
            ))
        return list(out.values())

    def fetch(self) -> list[RawJob]:
        base = self.require("url")
        code = self.options.get("country_code", "GB")
        modes = [("country filter", {"q": "", "optionsFacetsDD_country": code}),
                 ("location search", {"q": "", "locationsearch": self.search.countries[0]}),
                 ("all jobs", {"q": ""})]
        jobs: dict[str, RawJob] = {}
        for name, params in modes:
            first = self._page(base, params, 0)
            if not first:
                continue
            filtered = name != "all jobs"
            for job in first:
                jobs.setdefault(job.url, job)
            for page in range(1, MAX_PAGES):
                batch = self._page(base, params, page * self.PAGE)
                new = [j for j in batch if j.url not in jobs]
                for job in new:
                    jobs[job.url] = job
                if not new:
                    break
            self.note = name
            if filtered:
                in_uk = [j for j in jobs.values() if j.in_country is not False]
                if not in_uk:  # the site ignored the filter and nothing is in the UK
                    jobs.clear()
                    continue
                if len(in_uk) == len(jobs):  # the filter worked, so unlabelled jobs are UK too
                    for job in in_uk:
                        job.in_country = True
                self.scanned = len(jobs)
                return in_uk
            break
        if not jobs:
            raise SourceError("No jobs found on the SuccessFactors search page")
        self.scanned = len(jobs)
        return [j for j in jobs.values() if j.in_country is not False]


class SuccessFactorsCSBSource(Source):
    """Newer SAP SuccessFactors 'Career Site Builder' sites with a JSON jobs API."""

    type = "successfactors_csb"

    def fetch(self) -> list[RawJob]:
        base = self.require("url")
        jobs: dict[str, RawJob] = {}
        for page in range(MAX_PAGES):
            body = {"locale": "en_US", "pageNumber": page, "sortBy": "date", "keywords": "",
                    "location": self.search.countries[0], "facetFilters": {}, "brand": "",
                    "skills": [], "categoryId": 0, "alertId": "", "rcmCandidateId": ""}
            data = self.http.post(f"{base}/services/recruiting/v1/jobs", json=body,
                                  headers={"Accept": "application/json",
                                           "Content-Type": "application/json"}).json()
            results = data.get("jobSearchResult")
            if results is None:
                raise SourceError("Unexpected SuccessFactors response (no jobSearchResult)")
            for item in results:
                r = item.get("response", item)
                jid = str(r.get("id") or r.get("unifiedUrlTitle") or "")
                if not jid:
                    continue
                countries = r.get("jobLocationCountry") or []
                locs = [re.sub(r"<[^>]+>", "", x) for x in r.get("jobLocationShort") or []]
                loc = "; ".join(x.strip() for x in locs if x.strip())
                in_country = True if any(c in self.search.countries for c in countries) \
                    else self.where(f"{loc}; {'; '.join(countries)}")
                slug = htmllib.unescape(r.get("unifiedUrlTitle") or r.get("urlTitle") or "job")
                jobs.setdefault(jid, RawJob(
                    source_id=jid,
                    title=(r.get("unifiedStandardTitle") or r.get("title") or "").strip(),
                    url=f"{base}/job/{slug}/{jid}-en_US",
                    location=loc,
                    in_country=in_country,
                    posted=iso_date(r.get("unifiedStandardStart")),
                ))
            total = int(data.get("totalJobs") or 0)
            if not results or len(jobs) >= total:
                break
        self.scanned = len(jobs)
        return [j for j in jobs.values() if j.in_country is not False]


class RadancySource(Source):
    """Radancy (TalentBrew) career sites with /search-jobs (e.g. jobs.takeda.com)."""

    type = "radancy"
    PAGE = 100

    def fetch(self) -> list[RawJob]:
        base = self.require("url")
        jobs: dict[str, RawJob] = {}
        for page in range(1, MAX_PAGES + 1):
            data = self.http.get(
                f"{base}/search-jobs/results",
                params={"ActiveFacetID": 0, "CurrentPage": page, "RecordsPerPage": self.PAGE,
                        "Keywords": "", "Location": "", "SearchResultsModuleName": "Search Results",
                        "SearchFiltersModuleName": "Search Filters", "SortCriteria": 0,
                        "SortDirection": 0, "SearchType": 5},
                headers={"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"},
            ).json()
            soup = BeautifulSoup(data.get("results") or "", "html.parser")
            added = 0
            for a in soup.select("a[href*='/job/']"):
                href = urljoin(base + "/", a["href"])
                if href in jobs:
                    continue
                title_el = a.select_one("h2, h3, .job-title, [class*=title]")
                title = " ".join((title_el or a).get_text(" ").split())
                box = a.find_parent("li") or a
                loc_el = box.select_one(".job-location, [class*=location]")
                loc = " ".join(loc_el.get_text(" ").split()) if loc_el else ""
                date_el = box.select_one(".job-date-posted, [class*=date]")
                m = re.search(r"/(\d+)/?$", href)
                city = re.search(r"/job/([^/]+)/", href)
                hint = city.group(1).replace("-", " ") if city else ""
                jobs[href] = RawJob(
                    source_id=a.get("data-job-id") or (m.group(1) if m else href),
                    title=title,
                    url=href,
                    location=loc,
                    in_country=self.where(f"{loc} {hint}" if self.where(loc) is None else loc),
                    posted=iso_date(date_el.get_text(strip=True)) if date_el else None,
                )
                added += 1
            if not added or data.get("hasJobs") is False:
                break
        if not jobs:
            raise SourceError("No jobs found on the Radancy search page")
        self.scanned = len(jobs)
        return [j for j in jobs.values() if j.in_country is not False]


class ICIMSSource(Source):
    """iCIMS job portals (<name>.icims.com/jobs)."""

    type = "icims"

    def fetch(self) -> list[RawJob]:
        base = self.require("url")
        jobs: dict[str, RawJob] = {}
        for page in range(MAX_PAGES):
            html = self.http.get(f"{base}/jobs/search",
                                 params={"pr": page, "in_iframe": 1, "schemaId": "", "o": ""}).text
            soup = BeautifulSoup(html, "html.parser")
            added = 0
            for a in soup.find_all("a", href=re.compile(r"/jobs/\d+/[^/]+/job")):
                href = a["href"].split("?")[0]
                m = re.search(r"/jobs/(\d+)/", href)
                jid = m.group(1)
                if jid in jobs:
                    continue
                title_el = a.find(["h2", "h3"])
                title = " ".join((title_el or a).get_text(" ").split())
                title = re.sub(r"^Job Title\s*", "", title)
                if not title or title.lower() in {"apply", "view details"}:
                    continue
                box = a.find_parent(class_=re.compile(r"row|iCIMS_JobsTable")) or a.parent
                text = " ".join(box.get_text(" ").split()) if box else ""
                loc_m = re.search(r"Locations?\s*:?\s*(.{2,80}?)(?:\s{2,}|Category|Job ID|ID|Posted|$)",
                                  text)
                loc = loc_m.group(1).strip() if loc_m else text[:120]
                jobs[jid] = RawJob(source_id=jid, title=title, url=urljoin(base + "/", href),
                                   location=loc, in_country=self.where(loc))
                added += 1
            if not added:
                break
        if not jobs:
            raise SourceError("No jobs found on the iCIMS portal")
        self.scanned = len(jobs)
        return [j for j in jobs.values() if j.in_country is not False]


class AttraxSource(Source):
    """Attrax career sites that list vacancy tiles 10 per page (e.g. careers.abbvie.com)."""

    type = "attrax"

    def fetch(self) -> list[RawJob]:
        url = self.require("url")
        params = dict(self.options.get("params") or {})
        max_pages = int(self.options.get("max_pages", 150))
        jobs: dict[str, RawJob] = {}
        for page in range(1, max_pages + 1):
            html = self.http.get(url, params=dict(params, page=page),
                                 headers={"Accept": "text/html"}).text
            soup = BeautifulSoup(html, "html.parser")
            added = 0
            for tile in soup.select("div.attrax-vacancy-tile"):
                link = tile.select_one("a.attrax-vacancy-tile__title")
                if not link or not link.get("href"):
                    continue
                href = urljoin(url, link["href"])
                jid = tile.get("data-jobid") or href
                if jid in jobs:
                    continue
                free = tile.select_one(".attrax-vacancy-tile__location-freetext .attrax-vacancy-tile__item-value")
                country = tile.select_one(".attrax-vacancy-tile__option-location .attrax-vacancy-tile__item-value")
                loc = ", ".join(" ".join(el.get_text(" ").split()) for el in (free, country) if el)
                classes = " ".join(tile.get("class", []))
                # Tiles carry a class per location (e.g. attrax-vacancy-tile--united-kingdom),
                # which is more reliable than the free-text location.
                in_country = "--united-kingdom" in classes
                jobs[jid] = RawJob(source_id=str(jid), title=" ".join(link.get_text(" ").split()),
                                   url=href, location=loc, in_country=in_country)
                added += 1
            if not added:
                break
        if not jobs:
            raise SourceError("No vacancy tiles found on the page")
        # These sites only page through their newest few hundred roles.
        self.complete = False
        self.note = f"newest {len(jobs)} roles"
        self.scanned = len(jobs)
        return [j for j in jobs.values() if j.in_country is not False]


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
