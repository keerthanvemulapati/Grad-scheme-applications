"""Registry of job-board adapters."""
from __future__ import annotations

from .base import Source, SourceError
from .boards import (
    EightfoldSource,
    GreenhouseSource,
    JibeSource,
    LeverSource,
    PageWatchSource,
    PhenomSource,
    PinpointSource,
    SmartRecruitersSource,
    SuccessFactorsSource,
)
from .workday import WorkdaySource

REGISTRY: dict[str, type[Source]] = {
    cls.type: cls
    for cls in (
        WorkdaySource, EightfoldSource, JibeSource, PhenomSource, SuccessFactorsSource,
        GreenhouseSource, LeverSource, SmartRecruitersSource, PinpointSource, PageWatchSource,
    )
}


def build_source(company, cfg, search, session=None) -> Source:
    try:
        cls = REGISTRY[cfg.type]
    except KeyError:
        raise SourceError(f"Unknown source type '{cfg.type}' for {company.name}") from None
    return cls(company, cfg, search, session)


__all__ = ["REGISTRY", "Source", "SourceError", "build_source"]
