from tracker.config import Company, SourceConfig
from tracker.sources.workday import WorkdaySource, find_location_facet

from .conftest import FakeHTTP

FACETS = [
    {"facetParameter": "jobFamilyGroup", "values": [{"descriptor": "R&D", "id": "rd"}]},
    {"facetParameter": "locationMainGroup", "values": [
        {"facetParameter": "locationCountry", "descriptor": "Locations", "values": [
            {"descriptor": "United States of America", "id": "us"},
            {"descriptor": "United Kingdom", "id": "29247e57dbaf46fb855b224e03170bc7"},
        ]},
    ]},
]


def test_country_facet_preferred(search):
    assert find_location_facet(FACETS, search) == (
        "locationCountry", ["29247e57dbaf46fb855b224e03170bc7"], "country")


def test_hierarchy_facet_with_country_code_suffix(search):
    facets = [{"facetParameter": "locationMainGroup", "values": [
        {"facetParameter": "locations", "values": [{"descriptor": "Uxbridge - GB", "id": "ux"}]},
        {"facetParameter": "locationHierarchy2", "values": [
            {"descriptor": "United Kingdom (GB)", "id": "gb"}, {"descriptor": "France (FR)", "id": "fr"}]},
    ]}]
    assert find_location_facet(facets, search) == ("locationHierarchy2", ["gb"], "region")


def test_office_locations_used_when_no_country_facet(search):
    facets = [{"facetParameter": "locationMainGroup", "values": [
        {"facetParameter": "locations", "values": [
            {"descriptor": "UK - Cambridge", "id": "a"}, {"descriptor": "GBR - London - Moorgate", "id": "b"},
            {"descriptor": "High Wycombe, Buckinghamshire, United Kingdom", "id": "c"},
            {"descriptor": "Cambridge, MA", "id": "x"}, {"descriptor": "Kingsport, Tennessee", "id": "y"},
            {"descriptor": "CAN - British Columbia - Penticton", "id": "z"}]}]}]
    param, ids, kind = find_location_facet(facets, search)
    assert param == "locations" and ids == ["a", "b", "c"] and kind == "3 offices"
    assert find_location_facet([{"facetParameter": "timeType", "values": [{"descriptor": "Full", "id": "f"}]}],
                               search) is None


def _source(search, http):
    company = Company(name="GSK", type="pharma")
    cfg = SourceConfig(type="workday", key="gsk/workday",
                       options={"url": "https://gsk.wd5.myworkdayjobs.com/en-US/GSKCareers"})
    return WorkdaySource(company, cfg, search, session=http)


def test_workday_fetch_with_country_filter(search):
    pages = {
        0: {"total": 3, "facets": FACETS, "jobPostings": [
            {"title": "Regulatory Affairs Graduate Programme, UK, 2027",
             "externalPath": "/job/UK---London/Regulatory-Affairs-Graduate-Programme_427964",
             "locationsText": "UK - London", "postedOn": "Posted Today", "bulletFields": ["427964"]},
            {"title": "Senior Scientist", "externalPath": "/job/Stevenage/Senior-Scientist_R-1",
             "locationsText": "Stevenage", "postedOn": "Posted 30+ Days Ago"},
        ]},
        2: {"total": 0, "jobPostings": [
            {"title": "Medical Information Associate",
             "externalPath": "/job/Brentford/Medical-Information-Associate_R-2-1",
             "locationsText": "2 Locations", "postedOn": "Posted 3 Days Ago"},
        ]},
    }

    def jobs(method, url, kwargs):
        body = kwargs["json"]
        if not body["appliedFacets"] and body["offset"] == 0:
            return pages[0]
        assert body["appliedFacets"] == {"locationCountry": ["29247e57dbaf46fb855b224e03170bc7"]}
        return pages[body["offset"]] if body["offset"] in pages else pages[0]

    http = FakeHTTP({"/wday/cxs/gsk/GSKCareers/jobs": jobs})
    src = _source(search, http)
    found = {j.source_id: j for j in src.fetch()}
    assert set(found) == {"427964", "R-1", "R-2-1"}
    job = found["427964"]
    assert job.in_country is True
    assert job.url == ("https://gsk.wd5.myworkdayjobs.com/en-US/GSKCareers"
                       "/job/UK---London/Regulatory-Affairs-Graduate-Programme_427964")
    assert job.posted is not None
    assert found["R-1"].posted is None
    assert "country" in src.note


def test_workday_enrich_reads_advert(search):
    detail = {"jobPostingInfo": {
        "jobDescription": "<p>Start in <b>September 2027</b>. Recent graduates welcome.</p>",
        "location": "UK - London", "additionalLocations": ["UK - Stevenage"],
        "startDate": "2026-09-20", "country": {"descriptor": "United Kingdom"}}}
    http = FakeHTTP({"/job/UK---London/Reg_1": detail})
    src = _source(search, http)
    from tracker.models import RawJob
    job = RawJob(source_id="1", title="Reg", url="u", location="2 Locations", in_country=None,
                 extra={"path": "/job/UK---London/Reg_1"})
    job = src.enrich(job)
    assert job.enriched and job.in_country is True
    assert job.location == "UK - London; UK - Stevenage"
    assert job.posted == "2026-09-20"
    assert "September 2027" in job.description


def test_workday_fallback_keyword_search(search):
    def jobs(method, url, kwargs):
        body = kwargs["json"]
        if body["searchText"] == "":
            return {"total": 0, "facets": [], "jobPostings": []}
        if body["searchText"] == "regulatory":
            return {"total": 2, "jobPostings": [
                {"title": "Regulatory Affairs Associate", "externalPath": "/job/x/RA_1",
                 "locationsText": "London, United Kingdom"},
                {"title": "Regulatory Affairs Associate", "externalPath": "/job/y/RA_2",
                 "locationsText": "Paris, France"},
            ]}
        return {"total": 0, "jobPostings": []}

    src = _source(search, FakeHTTP({"/jobs": jobs}))
    found = {j.source_id: j for j in src.fetch()}
    assert found["1"].in_country is True
    assert found["2"].in_country is False
    assert "keyword" in src.note


def test_workday_retries_with_csrf_token(search):
    import requests

    from tracker.http import PoliteSession

    class Resp:
        def __init__(self, status, payload=None):
            self.status_code, self._payload, self.text = status, payload, ""

        def json(self):
            return self._payload

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError(response=self)

    http = PoliteSession(delay=0)
    seen = []

    def fake_post(url, **kw):
        seen.append(kw["headers"].get("X-CALYPSO-CSRF-TOKEN"))
        if not kw["headers"].get("X-CALYPSO-CSRF-TOKEN"):
            return Resp(422)
        return Resp(200, {"total": 0, "facets": [], "jobPostings": []})

    def fake_get(url, **kw):
        http.session.cookies.set("CALYPSO_CSRF_TOKEN", "tok")
        return Resp(200)

    http.session.post, http.session.get = fake_post, fake_get
    src = _source(search, http)
    assert src._page("", {}, 0)["total"] == 0
    assert seen == [None, "tok"]
