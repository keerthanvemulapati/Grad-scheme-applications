"""Loads the YAML configuration and compiles its patterns."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"


def _compile(patterns: list[str]) -> list[re.Pattern]:
    return [re.compile(p, re.IGNORECASE) for p in patterns or []]


@dataclass
class Category:
    key: str
    label: str
    priority: bool
    patterns: list[re.Pattern]


@dataclass
class SearchConfig:
    target_year: int
    countries: list[str]
    location_match: list[re.Pattern]
    location_places: list[re.Pattern]
    location_elsewhere: list[re.Pattern]
    location_ambiguous: list[re.Pattern]
    categories: list[Category]
    other_graduate_label: str
    scheme: list[re.Pattern]
    entry: list[re.Pattern]
    senior: list[re.Pattern]
    exclude: list[re.Pattern]
    exclude_functions: list[re.Pattern]
    register_interest: list[re.Pattern]
    fallback_queries: list[str]


@dataclass
class SourceConfig:
    type: str
    options: dict
    key: str = ""


@dataclass
class Company:
    name: str
    type: str
    careers_url: str = ""
    sources: list[SourceConfig] = field(default_factory=list)

    @property
    def slug(self) -> str:
        return slugify(self.name)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def load_search(path: Path | None = None) -> SearchConfig:
    data = yaml.safe_load((path or CONFIG_DIR / "search.yaml").read_text())
    loc = data.get("locations", {})
    return SearchConfig(
        target_year=int(data.get("target_intake_year", 2027)),
        countries=list(loc.get("countries", ["United Kingdom"])),
        location_match=_compile(loc.get("match")),
        location_places=_compile(loc.get("places")),
        location_elsewhere=_compile(loc.get("elsewhere")),
        location_ambiguous=_compile(loc.get("ambiguous")),
        categories=[
            Category(c["key"], c["label"], bool(c.get("priority")), _compile(c["patterns"]))
            for c in data["categories"]
        ],
        other_graduate_label=data.get("other_graduate_label", "Other Graduate Scheme"),
        scheme=_compile(data.get("scheme_patterns")),
        entry=_compile(data.get("entry_patterns")),
        senior=_compile(data.get("senior_patterns")),
        exclude=_compile(data.get("exclude_patterns")),
        exclude_functions=_compile(data.get("exclude_functions")),
        register_interest=_compile(data.get("register_interest_patterns")),
        fallback_queries=list(data.get("fallback_queries", [])),
    )


def load_companies(path: Path | None = None) -> list[Company]:
    data = yaml.safe_load((path or CONFIG_DIR / "companies.yaml").read_text())
    companies = []
    seen: set[str] = set()
    for entry in data["companies"]:
        company = Company(
            name=entry["name"],
            type=entry.get("type", "pharma"),
            careers_url=entry.get("careers_url", ""),
        )
        if company.slug in seen:
            raise ValueError(f"Duplicate company name in companies.yaml: {company.name}")
        seen.add(company.slug)
        for i, src in enumerate(entry.get("sources", [])):
            options = {k: v for k, v in src.items() if k != "type"}
            key = f"{company.slug}/{src['type']}" + (f"-{i + 1}" if i else "")
            company.sources.append(SourceConfig(type=src["type"], options=options, key=key))
        companies.append(company)
    return companies


def load_watchlist(path: Path | None = None) -> dict:
    p = path or CONFIG_DIR / "watchlist.yaml"
    if not p.exists():
        return {"programmes": [], "links": []}
    data = yaml.safe_load(p.read_text()) or {}
    return {"programmes": data.get("programmes", []), "links": data.get("links", [])}
