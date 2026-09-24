import json

from tracker.config import Company, SourceConfig
from tracker.sources import build_source

from .conftest import FakeHTTP


def make(search, type_, options, http, name="Acme"):
    company = Company(name=name, type="cro")
    return build_source(company, SourceConfig(type=type_, key=f"acme/{type_}", options=options),
                        search, session=http)


def test_phenom_reads_embedded_data(search):
    ddo = {"eagerLoadRefineSearch": {"totalHits": 2, "data": {"jobs": [
        {"jobId": "R1", "title": "Regulatory Affairs Graduate", "location": "Slough, UK",
         "country": "United Kingdom", "postedDate": "2026-09-10T00:00:00.000+0000"},
        {"jobId": "R2", "title": "Regulatory Affairs Associate", "location": "Brussels, Belgium",
         "country": "Belgium"},
    ]}}}
    html = f"<html><script>var phApp = phApp || {{}}; phApp.ddo = {json.dumps(ddo)}; phApp.x = 1;</script></html>"
    src = make(search, "phenom", {"url": "https://careers.acme.com/global/en"},
               FakeHTTP({"/widgets": {}, "search-results": html}))  # search API unusable -> page data
    jobs = {j.source_id: j for j in src.fetch()}
    assert src.note.startswith("page data") and not src.complete
    assert jobs["R1"].in_country is True and jobs["R1"].posted == "2026-09-10"
    assert jobs["R1"].url == "https://careers.acme.com/global/en/job/R1"
    assert jobs["R2"].in_country is False


def test_jibe_reads_api(search):
    payload = {"totalCount": 2, "jobs": [
        {"data": {"slug": "11844", "title": "Entry Level - Clinical Research Associate",
                  "city": "London", "country": "United Kingdom", "country_code": "GB",
                  "posted_date": "2026-09-01T00:00:00+0000", "description": "<p>Graduates welcome</p>"}},
        {"data": {"slug": "2", "title": "CRA", "city": "Cincinnati", "country": "United States",
                  "country_code": "US"}},
    ]}
    src = make(search, "jibe", {"url": "https://careers.medpace.com"}, FakeHTTP({"/api/jobs": payload}))
    jobs = {j.source_id: j for j in src.fetch()}
    assert jobs["11844"].in_country is True
    assert jobs["11844"].url == "https://careers.medpace.com/jobs/11844?lang=en-us"
    assert jobs["11844"].description == "Graduates welcome"
    assert jobs["2"].in_country is False


def test_successfactors_parses_rows(search):
    html = """
    <table id="searchresults"><tr class="data-row">
      <td><a class="jobTitle-link" href="/job/Bracknell-Regulatory-Affairs-Trainee/123456/">Regulatory Affairs Trainee</a></td>
      <td><span class="jobLocation">Bracknell, GB</span></td><td><span class="jobDate">12 Sept 2026</span></td>
    </tr></table>"""
    calls = []

    def page(method, url, kwargs):
        calls.append(kwargs["params"]["startrow"])
        return html if kwargs["params"]["startrow"] == 0 else "<table id='searchresults'></table>"

    src = make(search, "successfactors", {"url": "https://jobs.acme.com"}, FakeHTTP({"/search/": page}))
    jobs = src.fetch()
    assert len(jobs) == 1 and jobs[0].source_id == "123456"
    assert jobs[0].url == "https://jobs.acme.com/job/Bracknell-Regulatory-Affairs-Trainee/123456/"
    assert jobs[0].in_country is True


def test_pagewatch_finds_job_links(search):
    html = """
    <nav><a href="/careers">Careers</a><a href="/about">About us</a></nav>
    <ul>
      <li><a href="/careers/clinical-trials-assistant">Clinical Trials Assistant</a> London</li>
      <li><a href="/careers/research-physician">Research Physician</a></li>
      <li><a href="/vacancies/apply">Apply now</a></li>
      <li><a href="https://www.linkedin.com/company/hmr">LinkedIn</a></li>
    </ul>"""
    src = make(search, "pagewatch", {"url": "https://www.hmrlondon.com/careers", "uk_only": True},
               FakeHTTP({"hmrlondon.com": html}))
    titles = sorted(j.title for j in src.fetch())
    assert titles == ["Clinical Trials Assistant", "Research Physician"]


def test_greenhouse_and_lever(search):
    gh = {"jobs": [{"id": 1, "title": "Clinical Trial Assistant", "absolute_url": "https://gh/1",
                    "location": {"name": "Nottingham, UK"}, "first_published": "2026-09-01T10:00:00Z",
                    "content": "&lt;p&gt;Recent graduates&lt;/p&gt;"}]}
    src = make(search, "greenhouse", {"board": "acme"}, FakeHTTP({"boards-api.greenhouse.io": gh}))
    job = src.fetch()[0]
    assert job.in_country and job.posted == "2026-09-01" and job.description == "Recent graduates"

    lever = [{"id": "x", "text": "Regulatory Affairs Associate", "hostedUrl": "https://lever/x",
              "categories": {"location": "London"}, "createdAt": 1790000000000}]
    src = make(search, "lever", {"company": "acme"}, FakeHTTP({"api.lever.co": lever}))
    job = src.fetch()[0]
    assert job.in_country and job.posted.startswith("2026")


def test_pinpoint(search):
    payload = {"data": [{"id": 7, "title": "Clinical Trials Associate",
                         "url": "https://rp.pinpointhq.com/postings/7",
                         "location": {"name": "London Bridge"}}]}
    src = make(search, "pinpoint", {"url": "https://rp.pinpointhq.com", "uk_only": True},
               FakeHTTP({"postings.json": payload}))
    job = src.fetch()[0]
    assert job.title == "Clinical Trials Associate" and job.in_country is True


def test_successfactors_tile_layout_and_fallback(search):
    tiles = """
    <ul><li class="job-tile job-id-1"><a class="jobTitle-link" href="/job/Bracknell-Clinical-Trial-Assistant/1412878433/">Clinical Trial Assistant</a>
      <div class="section-field location"><div>Bracknell, GB</div></div></li>
    <li class="job-tile job-id-2"><a class="jobTitle-link" href="/job/Ingelheim-Scientist/1412878434/">Scientist</a>
      <div class="section-field location"><div>Ingelheim, DE</div></div></li></ul>"""

    def page(method, url, kwargs):
        params = kwargs["params"]
        if "optionsFacetsDD_country" in params or params["startrow"] > 0:
            return "<html></html>"  # facet not supported here; later pages empty
        return tiles

    src = make(search, "successfactors", {"url": "https://jobs.acme.com"}, FakeHTTP({"/search/": page}))
    jobs = src.fetch()
    assert [j.title for j in jobs] == ["Clinical Trial Assistant"]
    assert src.note == "location search"


def test_eightfold_filters_locally(search):
    payload = {"count": 2, "positions": [
        {"id": 1, "name": "Regulatory Affairs Graduate", "location": "Reading,Berkshire,United Kingdom"},
        {"id": 2, "name": "Regulatory Affairs Graduate", "location": "Berlin,Berlin,Germany"}]}
    src = make(search, "eightfold", {"url": "https://talent.acme.com", "domain": "acme.com"},
               FakeHTTP({"/api/apply/v2/jobs": payload}))
    jobs = src.fetch()
    assert [j.source_id for j in jobs] == ["1"] and jobs[0].in_country is True


def test_successfactors_csb(search):
    payload = {"totalJobs": 2, "jobSearchResult": [
        {"response": {"id": 5501, "unifiedStandardTitle": "Medical Information Associate",
                      "unifiedUrlTitle": "Medical-Information-Associate-Uxbridge",
                      "jobLocationShort": ["London, GBR, UB8 1DH<br/>"], "jobLocationCountry": ["United Kingdom"],
                      "unifiedStandardStart": "2026-09-20"}},
        {"response": {"id": 5502, "unifiedStandardTitle": "Scientist", "unifiedUrlTitle": "Scientist",
                      "jobLocationShort": ["Munich, DEU"], "jobLocationCountry": ["Germany"]}}]}
    src = make(search, "successfactors_csb", {"url": "https://careers.acme.com"},
               FakeHTTP({"/services/recruiting/v1/jobs": payload}))
    jobs = src.fetch()
    assert len(jobs) == 1 and jobs[0].title == "Medical Information Associate"
    assert jobs[0].url == "https://careers.acme.com/job/Medical-Information-Associate-Uxbridge/5501-en_US"
    assert jobs[0].location == "London, GBR, UB8 1DH" and jobs[0].posted == "2026-09-20"


def test_radancy(search):
    html = """<section id="search-results-list"><ul>
      <li><a href="/job/london/clinical-trial-administrator/1113/100001" data-job-id="100001">
        <h2>Clinical Trial Administrator</h2><span class="job-location">London, England, United Kingdom</span></a></li>
      <li><a href="/job/mumbai/medical-science-liaison/1113/100002" data-job-id="100002">
        <h2>Medical Science Liaison</h2><span class="job-location">Mumbai, India</span></a></li>
    </ul></section>"""

    def page(method, url, kwargs):
        return {"results": html if kwargs["params"]["CurrentPage"] == 1 else "", "hasJobs": True}

    src = make(search, "radancy", {"url": "https://jobs.acme.com"}, FakeHTTP({"search-jobs/results": page}))
    jobs = src.fetch()
    assert [(j.source_id, j.title) for j in jobs] == [("100001", "Clinical Trial Administrator")]
    assert jobs[0].url == "https://jobs.acme.com/job/london/clinical-trial-administrator/1113/100001"


def test_icims(search):
    html = """<div class="iCIMS_JobsTable">
      <div class="row"><div class="title"><a href="https://x.icims.com/jobs/11844/entry-level-cra/job?in_iframe=1">
        <h3>Entry Level - Clinical Research Associate</h3></a></div>
        <div class="header left"><span>Job Locations</span> <span>UK-London</span></div></div>
      <div class="row"><div class="title"><a href="https://x.icims.com/jobs/2/cra/job?in_iframe=1"><h3>CRA</h3></a></div>
        <div class="header left"><span>Job Locations</span> <span>US-OH-Cincinnati</span></div></div>
    </div>"""

    def page(method, url, kwargs):
        return html if kwargs["params"]["pr"] == 0 else "<div></div>"

    src = make(search, "icims", {"url": "https://x.icims.com"}, FakeHTTP({"/jobs/search": page}))
    jobs = src.fetch()
    assert [j.source_id for j in jobs] == ["11844"]
    assert jobs[0].title == "Entry Level - Clinical Research Associate"
    assert jobs[0].url == "https://x.icims.com/jobs/11844/entry-level-cra/job"


def test_attrax_tiles(search):
    tile = """<div class="attrax-vacancy-tile attrax-vacancy-tile--{cls}" data-jobid="{jid}">
      <a class="attrax-vacancy-tile__title" href="/en/job/{slug}-jid-{jid}">{title}</a>
      <div class="attrax-vacancy-tile__location-freetext"><p class="attrax-vacancy-tile__item-value"> {city} </p></div>
      <div class="attrax-vacancy-tile__option-location"><p class="attrax-vacancy-tile__item-value">{country}</p></div></div>"""
    page1 = tile.format(cls="united-kingdom", jid=1, slug="ra", title="Regulatory Affairs Associate",
                        city="Maidenhead", country="United Kingdom") + \
        tile.format(cls="netherlands", jid=2, slug="qa", title="QA Manager", city="Zwolle", country="Netherlands")

    def page(method, url, kwargs):
        return page1 if kwargs["params"]["page"] == 1 else "<div></div>"

    src = make(search, "attrax", {"url": "https://careers.acme.com/en/jobs"}, FakeHTTP({"/en/jobs": page}))
    jobs = src.fetch()
    assert [(j.source_id, j.location) for j in jobs] == [("1", "Maidenhead, United Kingdom")]
    assert not src.complete
    assert jobs[0].url == "https://careers.acme.com/en/job/ra-jid-1"


def test_phenom_search_api(search):
    page = '<script>phApp.ddo = {}; var x = {"csrfToken":"abc"};</script>'
    sent = []

    def widgets(method, url, kwargs):
        sent.append((kwargs["json"], kwargs["headers"].get("x-csrf-token")))
        return {"refineSearch": {"totalHits": 1, "data": {"jobs": [
            {"jobId": "93001", "title": "Regulatory Affairs Associate", "city": "Slough",
             "country": "United Kingdom", "postedDate": "2026-09-01T00:00:00.000+0000"}]}}}

    src = make(search, "phenom", {"url": "https://careers.acme.com/global/en"},
               FakeHTTP({"/widgets": widgets, "search-results": page}))
    jobs = src.fetch()
    assert [(j.source_id, j.in_country) for j in jobs] == [("93001", True)]
    payload, token = sent[0]
    assert token == "abc" and payload["lang"] == "en_global" and payload["country"] == "global"
    assert payload["selected_fields"] == {"country": ["United Kingdom"]}
    assert src.note == "search API filtered by country"
