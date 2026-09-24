"""Finds out which job-board platform a careers page uses.

Run on GitHub Actions (open internet) with:  python -m tracker probe
It prints a table you can use to add or fix entries in config/companies.yaml.
"""
from __future__ import annotations

import os
import re

from .config import load_companies
from .http import PoliteSession

FINGERPRINTS = {
    "workday": r"[\w-]+\.wd\d+\.myworkdayjobs\.com/[\w./-]*",
    "greenhouse": r"(?:boards|job-boards)(?:-api)?\.greenhouse\.io/[\w/-]+",
    "lever": r"jobs\.lever\.co/[\w-]+",
    "smartrecruiters": r"(?:careers|jobs)\.smartrecruiters\.com/[\w-]+",
    "eightfold": r"eightfold\.ai|/api/apply/v2/jobs",
    "phenom": r"phApp\.ddo|phenompeople|cdn\.phenompeople\.com",
    "jibe": r"jibecdn|/api/jobs\b|jibe\.com",
    "successfactors": r"successfactors\.(?:com|eu)|jobTitle-link|rmkcdn",
    "icims": r"[\w-]+\.icims\.com",
    "taleo": r"[\w-]+\.taleo\.net",
    "oracle": r"[\w.-]+\.oraclecloud\.com/hcmUI/CandidateExperience",
    "pinpoint": r"[\w-]+\.pinpointhq\.com",
    "workable": r"apply\.workable\.com/[\w-]+",
    "teamtailor": r"[\w-]+\.teamtailor\.com",
    "bamboohr": r"[\w-]+\.bamboohr\.com",
    "avature": r"avature\.net",
    "radancy": r"tbcdn\.talentbrew\.com|/search-jobs",
    "adp": r"myjobs\.adp\.com/[\w-]+",
}

EXTRA_PAGES = [
    "https://careers.abbvie.com/en/jobs",
    "https://careers.abbvie.com/en/search-results",
    "https://jobs.boehringer-ingelheim.com/",
    "https://careers.ucb.com/global/en",
    "https://talent.bayer.com/careers",
    "https://careers.teva/",
    "https://careers.astellas.com/?locale=en_US",
    "https://careers.novonordisk.com/",
    "https://www.novonordisk.co.uk/careers/find-a-job.html",
    "https://careers.medpace.com/jobs",
    "https://www.quotientsciences.com/careers",
    "https://richmondpharmacology.pinpointhq.com/",
    "https://careers.daiichisankyo.com/",
    "https://careers.viatris.com/",
    "https://jobs.organon.com/",
    "https://careers.kyowakirin.com/",
    "https://www.merckgroup.com/en/careers.html",
    "https://careers.cencora.com/us/en/united-kingdom-jobs",
]

WORKDAY_GUESSES = [
    "https://vrtx.wd5.myworkdayjobs.com/Vertex_Careers",
    "https://vrtx.wd501.myworkdayjobs.com/Vertex_Careers",
    "https://abbvie.wd1.myworkdayjobs.com/abbvie",
    "https://abbvie.wd5.myworkdayjobs.com/External",
    "https://boehringer.wd3.myworkdayjobs.com/Boehringer",
    "https://ucb.wd3.myworkdayjobs.com/UCB",
    "https://viatris.wd5.myworkdayjobs.com/Viatris",
    "https://organon.wd5.myworkdayjobs.com/OrganonCareers",
    "https://astellas.wd1.myworkdayjobs.com/Astellas",
    "https://teva.wd3.myworkdayjobs.com/TEVA",
    "https://sandoz.wd3.myworkdayjobs.com/Sandoz",
    "https://precisionmedicine.wd1.myworkdayjobs.com/PrecisionForMedicine",
    "https://daiichisankyo.wd1.myworkdayjobs.com/DSE",
    "https://jazz.wd5.myworkdayjobs.com/JazzCareers",
    "https://beigene.wd5.myworkdayjobs.com/BeiGene",
    "https://kyowakirin.wd3.myworkdayjobs.com/External",
]


def fingerprint(html: str) -> str:
    hits = []
    for name, pattern in FINGERPRINTS.items():
        found = sorted(set(re.findall(pattern, html)))[:3]
        if found:
            hits.append(f"{name}: {', '.join(found)[:160]}")
    return "; ".join(hits) or "no known platform found"


def main() -> None:
    http = PoliteSession(delay=0.2)
    rows = ["| Page | Status | Platform hints |", "|---|---|---|"]
    pages = [c.careers_url for c in load_companies() if c.careers_url] + EXTRA_PAGES
    for url in dict.fromkeys(pages):
        try:
            resp = http.session.get(url, timeout=25)
            rows.append(f"| {url} | {resp.status_code} → {resp.url[:70]} | "
                        f"{fingerprint(resp.text).replace('|', '/')} |")
        except Exception as exc:  # noqa: BLE001
            rows.append(f"| {url} | error | {type(exc).__name__}: {str(exc)[:120]} |")
    rows += ["", "| Workday guess | Result |", "|---|---|"]
    for url in WORKDAY_GUESSES:
        host, site = url.split("/")[2], url.split("/")[3]
        api = f"https://{host}/wday/cxs/{host.split('.')[0]}/{site}/jobs"
        try:
            resp = http.session.post(api, json={"appliedFacets": {}, "limit": 1, "offset": 0,
                                                "searchText": ""}, timeout=25)
            total = resp.json().get("total") if resp.ok else None
            rows.append(f"| {url} | HTTP {resp.status_code}, total={total} |")
        except Exception as exc:  # noqa: BLE001
            rows.append(f"| {url} | error {type(exc).__name__} |")
    report = "\n".join(rows)
    print(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as fh:
            fh.write("## Job board probe\n\n" + report + "\n")
