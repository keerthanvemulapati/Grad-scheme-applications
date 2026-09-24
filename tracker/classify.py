"""Decides whether a job is relevant, what area it is in, and how junior it is."""
from __future__ import annotations

import re

from .config import SearchConfig
from .models import Classification

YEAR_RE = re.compile(r"\b(20[2-3]\d)\b")
EXPERIENCE_RE = re.compile(
    r"(\d{1,2})\s*\+?\s*(?:-|–|to)?\s*(?:\d{1,2}\s*)?\+?\s*years?[’'`]?\s+"
    r"(?:of\s+)?(?:(?:relevant|proven|industry|professional|previous|prior|hands[- ]on|"
    r"practical|demonstrable|direct|clinical|pharmaceutical|work|working)\s+)*"
    r"(?:experience|exp\b)",
    re.IGNORECASE,
)
GRAD_FRIENDLY_RE = re.compile(
    r"no\s+(?:prior\s+|previous\s+)?experience\s+(?:is\s+)?(?:required|necessary|needed)|"
    r"recent\s+graduates?|new\s+graduates?|graduating\s+in|final[- ]year|"
    r"degree\s+(?:due|expected)\s+(?:in\s+)?20\d\d|entry[- ]level",
    re.IGNORECASE,
)

LEVEL_POINTS = {"graduate_scheme": 30, "entry_level": 20, "check": 0}


def _any(patterns: list[re.Pattern], text: str) -> bool:
    return any(p.search(text) for p in patterns)


def location_status(text: str, cfg: SearchConfig) -> bool | None:
    """True if the location text is in a target country, False if clearly not, None if unclear."""
    text = text or ""
    if _any(cfg.location_match, text):
        return True
    if _any(cfg.location_ambiguous, text):
        return None
    return False


def extract_facts(description: str, cfg: SearchConfig) -> dict:
    """Pull the few facts we need out of an advert, so the full text needn't be stored."""
    description = description or ""
    years = [int(m) for m in EXPERIENCE_RE.findall(description)]
    years = [y for y in years if 0 < y <= 15]
    return {
        "min_years": min(years) if years else None,
        "graduate_friendly": bool(GRAD_FRIENDLY_RE.search(description)),
        "mentions_target_year": str(cfg.target_year) in description,
    }


def classify(
    title: str,
    cfg: SearchConfig,
    facts: dict | None = None,
    in_country: bool | None = True,
) -> Classification:
    """Classify a job from its title, plus facts from the advert when we have them."""
    t = " ".join((title or "").split())
    if not t:
        return Classification(False, reason="empty title")
    if in_country is False:
        return Classification(False, reason="outside target countries")
    if _any(cfg.exclude, t):
        return Classification(False, reason="internship/placement/student role")

    is_scheme = _any(cfg.scheme, t)
    if not is_scheme and _any(cfg.senior, t):
        return Classification(False, reason="too senior or needs a professional qualification")

    category = None
    for cat in cfg.categories:
        if _any(cat.patterns, t):
            category = cat
            break

    if category is not None:
        key, label, priority = category.key, category.label, category.priority
    elif is_scheme and not _any(cfg.exclude_functions, t):
        key, label, priority = "other_graduate", cfg.other_graduate_label, False
    else:
        return Classification(False, reason="not a target area")

    if is_scheme:
        level = "graduate_scheme"
    elif _any(cfg.entry, t):
        level = "entry_level"
    else:
        level = "check"

    tags: list[str] = []
    target = str(cfg.target_year)
    title_years = set(YEAR_RE.findall(t))
    if target in title_years:
        tags.append(target)
    elif title_years and max(int(y) for y in title_years) < cfg.target_year:
        tags.append("old_intake")
    if _any(cfg.register_interest, t):
        tags.append("register_interest")

    if facts:
        if facts.get("mentions_target_year") and target not in tags and "old_intake" not in tags:
            tags.append(target)
        min_years = facts.get("min_years")
        grad_friendly = bool(facts.get("graduate_friendly"))
        if min_years and min_years >= 2 and level != "graduate_scheme":
            tags.append("experience_required")
        elif grad_friendly:
            if level == "check":
                level = "entry_level"
            tags.append("graduate_friendly")
    if in_country is None:
        tags.append("location_unclear")

    # Roles of unclear seniority are only kept for the areas you care about most.
    if level == "check" and not priority and key != "drug_safety":
        return Classification(False, reason="unclear seniority outside priority areas")

    score = (100 if priority else 40) + LEVEL_POINTS[level]
    if target in tags:
        score += 15
    if "register_interest" in tags:
        score += 5
    if "graduate_friendly" in tags:
        score += 5
    if "experience_required" in tags:
        score -= 25
    if "old_intake" in tags:
        score -= 60

    return Classification(
        relevant=True,
        category=key,
        category_label=label,
        priority=priority,
        level=level,
        tags=tags,
        score=score,
    )
