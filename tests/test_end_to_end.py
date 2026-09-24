"""Runs the whole `tracker run` command against a fake job board."""
import json

import tracker.__main__ as cli
from tracker import render, store
from tracker.config import Company, SourceConfig
from tracker.models import RawJob
from tracker.runner import run_source


class FakeSource:
    supports_enrich = True
    note = "fake"

    def __init__(self, jobs):
        self._jobs = jobs
        self.scanned = 0
        self.enriched = []

    def fetch(self):
        self.scanned = len(self._jobs)
        return [RawJob(**j) for j in self._jobs]

    def enrich(self, job):
        self.enriched.append(job.source_id)
        job.description = "Open to recent graduates. Starts September 2027."
        job.enriched = True
        job.in_country = True
        return job


def test_run_source_classifies_and_enriches(search, monkeypatch):
    fake = FakeSource([
        {"source_id": "1", "title": "Regulatory Affairs Graduate Programme", "url": "u1",
         "location": "2 Locations", "in_country": None},
        {"source_id": "2", "title": "Senior Director, Regulatory", "url": "u2", "in_country": True},
        {"source_id": "3", "title": "Clinical Trial Assistant", "url": "u3", "in_country": True},
    ])
    monkeypatch.setattr("tracker.runner.build_source", lambda *a, **k: fake)
    company = Company(name="GSK", type="pharma")
    result = run_source(company, SourceConfig("workday", {}, "gsk/workday"), search, known={})
    assert result.ok and result.scanned == 3
    ids = {j["id"]: j for j in result.jobs}
    assert set(ids) == {"gsk:1", "gsk:3"}
    assert "2027" in ids["gsk:1"]["tags"] and ids["gsk:1"]["facts"]["graduate_friendly"]
    assert fake.enriched == ["1", "3"]

    # Second run: adverts already read are not fetched again.
    fake.enriched.clear()
    result = run_source(company, SourceConfig("workday", {}, "gsk/workday"), search, known=ids)
    assert fake.enriched == []
    assert "2027" in {j["id"]: j for j in result.jobs}["gsk:1"]["tags"]


def test_cli_run_writes_outputs_and_alerts(tmp_path, monkeypatch, search):
    for name, attr in ((store, "STATE_PATH"), (store, "HEALTH_PATH"), (render, "README_PATH"),
                       (render, "DASHBOARD_DATA"), (render, "FEED_PATH")):
        monkeypatch.setattr(name, attr, tmp_path / f"{attr.lower()}.out")
    (tmp_path / "readme_path.out").write_text(f"# Intro\n{render.START}\n{render.END}\n")

    boards = [[{"source_id": "1", "title": "Medical Affairs Graduate Programme 2027", "url": "u1",
                "location": "London", "in_country": True}]]
    monkeypatch.setattr("tracker.runner.build_source", lambda *a, **k: FakeSource(boards[-1]))
    company = Company(name="MSD", type="pharma",
                      sources=[SourceConfig("workday", {}, "msd/workday")])
    monkeypatch.setattr(cli, "load_companies", lambda: [company])
    announced = []
    monkeypatch.setattr(cli.notify, "announce",
                        lambda jobs, title, intro: announced.append((title, jobs)) or {"number": 1})
    monkeypatch.setenv("TRACKER_NOTIFY", "1")

    class Args:
        only = None
        no_notify = False
        dry_run = False

    assert cli.cmd_run(Args) == 0
    state = json.loads((tmp_path / "state_path.out").read_text())
    assert list(state["jobs"]) == ["msd:1"] and state["meta"]["snapshot_issue"] == 1
    assert announced and announced[0][0].startswith("Tracker is live: 1 open roles")
    readme = (tmp_path / "readme_path.out").read_text()
    assert readme.startswith("# Intro") and "Medical Affairs Graduate Programme 2027" in readme

    boards.append(boards[0] + [{"source_id": "2", "title": "Regulatory Affairs Associate",
                                "url": "u2", "location": "London", "in_country": True}])
    announced.clear()
    assert cli.cmd_run(Args) == 0
    assert len(announced) == 1 and announced[0][0].startswith("New: MSD – Regulatory Affairs Associate")
    assert [j["id"] for j in announced[0][1]] == ["msd:2"]

    # Nothing new and just refreshed: files are left alone.
    before = (tmp_path / "state_path.out").read_text()
    announced.clear()
    assert cli.cmd_run(Args) == 0
    assert not announced and (tmp_path / "state_path.out").read_text() == before
