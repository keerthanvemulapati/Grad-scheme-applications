"""Plain data containers shared across the tracker."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RawJob:
    """A job as read from a job board, before classification."""

    source_id: str
    title: str
    url: str
    location: str = ""
    # True: confirmed in a target country. False: confirmed outside. None: unknown.
    in_country: bool | None = None
    posted: str | None = None  # ISO date (YYYY-MM-DD)
    description: str = ""
    enriched: bool = False
    extra: dict = field(default_factory=dict)


@dataclass
class Classification:
    relevant: bool
    category: str = ""
    category_label: str = ""
    priority: bool = False
    level: str = ""  # graduate_scheme | entry_level | check
    tags: list[str] = field(default_factory=list)
    score: int = 0
    reason: str = ""


@dataclass
class SourceResult:
    company: str
    source_key: str
    source_type: str
    ok: bool
    jobs: list[dict] = field(default_factory=list)
    scanned: int = 0
    error: str | None = None
    duration: float = 0.0
    note: str = ""
    # False when the board only showed part of its jobs (e.g. the newest few hundred),
    # so a role missing from this run hasn't necessarily closed.
    complete: bool = True
