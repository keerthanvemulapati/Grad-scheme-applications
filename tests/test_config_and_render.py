import datetime as dt

from tracker import render
from tracker.config import load_companies, load_watchlist
from tracker.sources import REGISTRY, build_source


def test_every_configured_board_builds(search):
    companies = load_companies()
    assert len(companies) >= 30
    keys = set()
    for company in companies:
        assert company.sources, company.name
        assert company.type in {"pharma", "cro", "consultancy"}
        for src in company.sources:
            assert src.type in REGISTRY
            build_source(company, src, search)  # raises on a malformed entry
            assert src.key not in keys
            keys.add(src.key)


def test_watchlist_entries_have_links():
    w = load_watchlist()
    assert w["programmes"]
    for p in w["programmes"]:
        assert p["url"].startswith("https://") and p["company"] and p["programme"]


def _state():
    today = dt.date(2026, 9, 24).isoformat()
    job = {"id": "gsk:1", "company": "GSK", "company_type": "pharma",
           "title": "Regulatory Affairs Graduate Programme | UK 2027", "url": "https://x/1",
           "location": "UK - London", "posted": today, "category": "regulatory_affairs",
           "category_label": "Regulatory Affairs", "priority": True, "level": "graduate_scheme",
           "tags": ["2027"], "score": 145, "first_seen": today, "last_seen": today,
           "status": "open", "closed_on": None}
    old = dict(job, id="gsk:2", title="Regulatory Affairs Graduate Programme 2026",
               tags=["old_intake"], score=70)
    closed = dict(job, id="gsk:3", title="Clinical Trial Assistant", status="closed",
                  closed_on=today, category="clinical_operations",
                  category_label="Clinical Operations", level="entry_level", tags=[])
    return {"meta": {}, "jobs": {j["id"]: j for j in (job, old, closed)}}


def test_readme_section(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "someone/Grad-scheme-applications")
    now = dt.datetime(2026, 9, 24, 9, 0, tzinfo=dt.timezone.utc)
    health = {"gsk/workday": {"company": "GSK", "type": "workday", "ok": True, "scanned": 300,
                              "matches": 3, "note": "filtered by country"}}
    text = render.build_readme_section(_state(), health, load_watchlist(), now)
    assert text.startswith(render.START) and text.endswith(render.END)
    assert "**1 open roles**" in text
    assert "https://someone.github.io/Grad-scheme-applications/" in text
    assert "Regulatory Affairs Graduate Programme / UK 2027" in text  # pipe escaped
    assert "### Regulatory Affairs (1)" in text
    assert "earlier-intake" in text and "Closed recently" in text
    assert "1 of 1 job boards" in text


def test_write_readme_keeps_intro(tmp_path, monkeypatch):
    path = tmp_path / "README.md"
    path.write_text(f"# Intro\n\nHello\n\n{render.START}\nold\n{render.END}\n\nFooter\n")
    monkeypatch.setattr(render, "README_PATH", path)
    render.write_readme(f"{render.START}\nnew\n{render.END}")
    assert path.read_text() == f"# Intro\n\nHello\n\n{render.START}\nnew\n{render.END}\n\nFooter\n"


def test_feed_and_dashboard(tmp_path, monkeypatch):
    monkeypatch.setattr(render, "FEED_PATH", tmp_path / "feed.xml")
    monkeypatch.setattr(render, "DASHBOARD_DATA", tmp_path / "jobs.json")
    now = dt.datetime(2026, 9, 24, 9, 0, tzinfo=dt.timezone.utc)
    render.write_feed(_state(), now)
    render.write_dashboard_data(_state(), {}, load_watchlist(), now)
    feed = (tmp_path / "feed.xml").read_text()
    assert feed.count("<item>") == 1 and "GSK — Regulatory Affairs" in feed
    state = _state()
    state["jobs"]["gsk:1"]["baseline"] = True
    render.write_feed(state, now)
    assert (tmp_path / "feed.xml").read_text().count("<item>") == 0
    assert '"generated": "2026-09-24T09:00:00Z"' in (tmp_path / "jobs.json").read_text()
