import datetime as dt

from tracker import store
from tracker.models import SourceResult

DAY1, DAY2, DAY3 = dt.date(2026, 9, 24), dt.date(2026, 9, 25), dt.date(2026, 9, 26)


def rec(jid, key="gsk/workday", **kw):
    base = {"id": jid, "company": "GSK", "company_type": "pharma", "title": f"Role {jid}",
            "url": f"https://x/{jid}", "location": "London", "in_country": True, "posted": None,
            "category": "regulatory_affairs", "category_label": "Regulatory Affairs",
            "priority": True, "level": "graduate_scheme", "tags": [], "score": 130,
            "facts": None, "source_key": key, "source_type": "workday"}
    base.update(kw)
    return base


def result(jobs, ok=True, key="gsk/workday"):
    return SourceResult(company="GSK", source_key=key, source_type="workday", ok=ok,
                        jobs=[dict(j) for j in jobs])


KEYS = {"gsk/workday", "az/workday"}


def test_first_run_is_silent_then_new_roles_alert():
    state = store.empty_state()
    changes = store.merge(state, [result([rec("a"), rec("b")])], DAY1, KEYS)
    assert not changes["new"] and len(changes["silent"]) == 2
    changes = store.merge(state, [result([rec("a"), rec("b"), rec("c")])], DAY2, KEYS)
    assert [j["id"] for j in changes["new"]] == ["c"]
    assert state["jobs"]["c"]["first_seen"] == DAY2.isoformat()
    assert state["jobs"]["a"]["first_seen"] == DAY1.isoformat()


def test_role_closes_after_two_missed_runs_and_can_reopen():
    state = store.empty_state()
    store.merge(state, [result([rec("a"), rec("b")])], DAY1, KEYS)
    store.merge(state, [result([rec("a")])], DAY2, KEYS)
    assert state["jobs"]["b"]["status"] == "open" and state["jobs"]["b"]["missed"] == 1
    changes = store.merge(state, [result([rec("a")])], DAY3, KEYS)
    assert [j["id"] for j in changes["closed"]] == ["b"]
    assert state["jobs"]["b"]["status"] == "closed"
    changes = store.merge(state, [result([rec("a"), rec("b")])], DAY3, KEYS)
    assert [j["id"] for j in changes["reopened"]] == ["b"]
    assert state["jobs"]["b"]["status"] == "open"


def test_failed_board_does_not_close_its_roles():
    state = store.empty_state()
    store.merge(state, [result([rec("a")])], DAY1, KEYS)
    for day in (DAY2, DAY3):
        store.merge(state, [result([], ok=False)], day, KEYS)
    assert state["jobs"]["a"]["status"] == "open"


def test_new_board_is_added_silently():
    state = store.empty_state()
    store.merge(state, [result([rec("a")])], DAY1, KEYS)
    changes = store.merge(state, [result([rec("a")]),
                                  result([rec("z", key="az/workday")], key="az/workday")], DAY2, KEYS)
    assert not changes["new"] and [j["id"] for j in changes["silent"]] == ["z"]


def test_sticky_fields_survive_vaguer_updates():
    state = store.empty_state()
    store.merge(state, [result([rec("a", posted="2026-09-20", facts={"min_years": None})])], DAY1, KEYS)
    store.merge(state, [result([rec("a", posted=None, facts=None)])], DAY2, KEYS)
    assert state["jobs"]["a"]["posted"] == "2026-09-20"
    assert state["jobs"]["a"]["facts"] == {"min_years": None}


def test_roles_from_removed_companies_are_dropped():
    state = store.empty_state()
    store.merge(state, [result([rec("a")])], DAY1, KEYS)
    store.merge(state, [], DAY2, {"az/workday"})
    assert state["jobs"] == {}


def test_health_counts_failures():
    health = {}
    store.update_health(health, [result([rec("a")])], DAY1, KEYS)
    assert health["gsk/workday"]["ok"] and health["gsk/workday"]["matches"] == 1
    failing = result([], ok=False)
    failing.error = "HTTPError: 500"
    store.update_health(health, [failing], DAY2, KEYS)
    store.update_health(health, [failing], DAY3, KEYS)
    assert health["gsk/workday"]["failures_in_a_row"] == 2
    assert health["gsk/workday"]["matches"] == 1
    assert health["gsk/workday"]["last_ok"] == DAY1.isoformat()


def test_partial_boards_expire_instead_of_closing():
    import datetime as dt

    state = store.empty_state()
    store.merge(state, [result([rec("a"), rec("b")])], DAY1, KEYS)
    partial = result([rec("a")])
    partial.complete = False
    for day in (DAY2, DAY3):
        store.merge(state, [partial], day, KEYS)
    assert state["jobs"]["b"]["status"] == "open"
    later = DAY1 + dt.timedelta(days=store.PARTIAL_EXPIRY_DAYS + 1)
    changes = store.merge(state, [partial], later, KEYS)
    assert [j["id"] for j in changes["closed"]] == ["b"]
