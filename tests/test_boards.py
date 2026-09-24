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
               FakeHTTP({"search-results": html}))
    jobs = {j.source_id: j for j in src.fetch()}
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
