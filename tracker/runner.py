"""Runs every job board, classifies what it finds and returns per-board results."""
from __future__ import annotations

import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from .classify import classify, extract_facts
from .config import Company, SearchConfig
from .models import RawJob, SourceResult
from .sources import SourceError, build_source

log = logging.getLogger("tracker")
ENRICH_BUDGET = 120  # full adverts fetched per board per run; the rest wait for the next run


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def build_record(company: Company, source_key: str, source_type: str, raw: RawJob,
                 cls, facts, in_country) -> dict:
    return {
        "id": f"{company.slug}:{raw.source_id}",
        "company": company.name,
        "company_type": company.type,
        "title": raw.title,
        "url": raw.url,
        "location": raw.location,
        "in_country": in_country,
        "posted": raw.posted,
        "category": cls.category,
        "category_label": cls.category_label,
        "priority": cls.priority,
        "level": cls.level,
        "tags": cls.tags,
        "score": cls.score,
        "facts": facts,
        "source_key": source_key,
        "source_type": source_type,
    }


def run_source(company: Company, src_cfg, search: SearchConfig, known: dict) -> SourceResult:
    started = time.monotonic()
    result = SourceResult(company=company.name, source_key=src_cfg.key,
                          source_type=src_cfg.type, ok=False)
    try:
        source = build_source(company, src_cfg, search)
        raw_jobs = source.fetch()
        result.scanned = source.scanned
        budget = ENRICH_BUDGET
        seen_titles: set[tuple[str, str]] = set()
        for raw in raw_jobs:
            jid = f"{company.slug}:{raw.source_id}"
            prev = known.get(jid) or {}
            facts = prev.get("facts")
            in_country = raw.in_country
            if in_country is None and prev.get("in_country") is not None:
                in_country = prev["in_country"]
            cls = classify(raw.title, search, facts=facts, in_country=in_country)
            if not cls.relevant:
                continue
            if facts is None and raw.description:
                facts = extract_facts(raw.description, search)
            elif facts is None and source.supports_enrich and budget > 0:
                budget -= 1
                try:
                    raw = source.enrich(raw)
                    facts = extract_facts(raw.description, search)
                    in_country = raw.in_country
                except Exception as exc:  # keep the role; try the advert again next run
                    log.warning("  could not read advert %s: %s", raw.url, exc)
            if prev.get("facts") is not None and not raw.enriched:
                raw.location = prev.get("location") or raw.location
                raw.posted = raw.posted or prev.get("posted")
            if in_country is not True:
                continue  # location unknown or elsewhere; a board that can say will be re-read next run
            cls = classify(raw.title, search, facts=facts, in_country=in_country)
            if not cls.relevant:
                continue
            dedupe_key = (_norm(raw.title), _norm(raw.location))
            if dedupe_key in seen_titles:
                continue
            seen_titles.add(dedupe_key)
            result.jobs.append(
                build_record(company, src_cfg.key, src_cfg.type, raw, cls, facts, in_country))
        result.ok = True
        result.note = source.note
        result.complete = source.complete
    except SourceError as exc:
        result.error = str(exc)
    except Exception as exc:  # network errors, unexpected page layouts...
        result.error = f"{type(exc).__name__}: {exc}"[:300]
    result.duration = round(time.monotonic() - started, 1)
    return result


def run_all(companies: list[Company], search: SearchConfig, known: dict,
            only: set[str] | None = None, workers: int = 8) -> list[SourceResult]:
    tasks = [(c, s) for c in companies for s in c.sources
             if not only or c.slug in only or c.name.lower() in only]
    results: list[SourceResult] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run_source, c, s, search, known): s.key for c, s in tasks}
        for fut in as_completed(futures):
            r = fut.result()
            status = "ok " if r.ok else "ERR"
            log.info("%s %-45s scanned=%-5s matches=%-3s %5.1fs %s", status, r.source_key,
                     r.scanned, len(r.jobs), r.duration, r.error or r.note)
            results.append(r)
    results.sort(key=lambda r: r.source_key)
    return results
