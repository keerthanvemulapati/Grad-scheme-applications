"""Temporary diagnostics for job boards that failed or under-reported. Deleted once fixed."""
import json
import re
import sys

import requests

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
      "Accept-Language": "en-GB,en;q=0.9"}
BROWSER = dict(UA, **{"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                      "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Site": "none", "Upgrade-Insecure-Requests": "1"})
s = requests.Session()


def section(t):
    print(f"\n===== {t} =====", flush=True)


def show(resp, n=600):
    print("status", resp.status_code, "server", resp.headers.get("server"), "ctype", resp.headers.get("content-type"))
    print(resp.text[:n].replace("\n", " "))


def walk(facets, path=""):
    for f in facets or []:
        if not isinstance(f, dict):
            continue
        param = f.get("facetParameter")
        vals = f.get("values") or []
        if param:
            hits = [f"{v.get('descriptor')}={v.get('id')}({v.get('count')})" for v in vals
                    if isinstance(v, dict) and re.search(r"king|brit|\bUK\b|england|\bGB", v.get("descriptor") or "", re.I)]
            print(f"  facet {path}{param}: {len(vals)} values; UK-ish: {hits[:6]}")
            walk(vals, path + param + ">")


def workday(url):
    host, site = url.split("/")[2], url.split("/")[3]
    api = f"https://{host}/wday/cxs/{host.split('.')[0]}/{site}/jobs"
    section(f"workday {url}")
    try:
        r = s.post(api, json={"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""},
                   headers=dict(UA, Accept="application/json"), timeout=30)
        if r.status_code != 200:
            show(r)
            return
        d = r.json()
        print("total", d.get("total"))
        walk(d.get("facets"))
    except Exception as e:  # noqa
        print("error", e)


for u in ["https://astrazeneca.wd3.myworkdayjobs.com/Careers", "https://astrazeneca.wd3.myworkdayjobs.com/Emerging-Talent",
          "https://jj.wd5.myworkdayjobs.com/JJ", "https://bristolmyerssquibb.wd5.myworkdayjobs.com/BMS",
          "https://msd.wd5.myworkdayjobs.com/SearchJobs", "https://thermofisher.wd5.myworkdayjobs.com/ThermoFisherCareers",
          "https://labcorp.wd1.myworkdayjobs.com/External", "https://roche.wd3.myworkdayjobs.com/roche-ext",
          "https://sanofi.wd3.myworkdayjobs.com/SanofiCareers", "https://pfizer.wd1.myworkdayjobs.com/PfizerCareers",
          "https://gsk.wd5.myworkdayjobs.com/GSKCareers", "https://lilly.wd5.myworkdayjobs.com/LLY",
          "https://takeda.wd3.myworkdayjobs.com/External", "https://gilead.wd1.myworkdayjobs.com/gileadcareers",
          "https://beigene.wd5.myworkdayjobs.com/BeiGene"]:
    workday(u)

section("medpace jibe")
for params in ({}, {"page": 1}, {"page": 1, "limit": 10}, {"page": 1, "location": "London"}):
    try:
        r = s.get("https://careers.medpace.com/api/jobs", params=params, headers=dict(UA, Accept="application/json"), timeout=30)
        print(params, r.status_code, r.text[:300].replace("\n", " "))
        try:
            d = r.json()
            print("  keys", list(d)[:10], "count", d.get("totalCount"), "n", len(d.get("jobs", [])))
            if d.get("jobs"):
                print("  first", json.dumps(d["jobs"][0])[:700])
        except Exception:
            pass
    except Exception as e:  # noqa
        print(params, "error", e)

section("eightfold bayer / teva")
for base, dom in (("https://talent.bayer.com", "bayer.com"), ("https://www.careers.teva", "teva.com"),
                  ("https://www.careers.teva", "careers.teva")):
    for loc in (None, "United Kingdom"):
        p = {"domain": dom, "start": 0, "num": 5}
        if loc:
            p["location"] = loc
        try:
            r = s.get(f"{base}/api/apply/v2/jobs", params=p, headers=dict(UA, Accept="application/json"), timeout=30)
            d = r.json() if "json" in (r.headers.get("content-type") or "") else {}
            pos = d.get("positions") or []
            print(base, dom, loc, r.status_code, "count", d.get("count"), "n", len(pos),
                  [(x.get("name"), x.get("location")) for x in pos[:3]], r.text[:200] if not d else "")
        except Exception as e:  # noqa
            print(base, dom, loc, "error", e)

section("successfactors CSB API")
body = {"locale": "en_US", "pageNumber": 0, "sortBy": "", "keywords": "", "location": "United Kingdom",
        "facetFilters": {}, "brand": "", "skills": [], "categoryId": 0, "alertId": "", "rcmCandidateId": ""}
for base in ("https://jobs.boehringer-ingelheim.com", "https://careers.novonordisk.com", "https://careers.astellas.com",
             "https://careers.daiichisankyo.com"):
    try:
        home = s.get(base + "/", headers=BROWSER, timeout=30)
        csrf = re.search(r'csrfToken\s*[:=]\s*"([^"]+)"', home.text)
        print(base, "home", home.status_code, "csrf", bool(csrf))
        hdr = dict(UA, Accept="application/json", **{"Content-Type": "application/json"})
        if csrf:
            hdr["X-CSRF-Token"] = csrf.group(1)
        r = s.post(base + "/services/recruiting/v1/jobs", json=body, headers=hdr, timeout=30)
        print("  api", r.status_code, r.text[:500].replace("\n", " "))
        r2 = s.get(base + "/search/", params={"q": "", "locationsearch": "United Kingdom"}, headers=BROWSER, timeout=30)
        print("  /search/", r2.status_code, "data-row" in r2.text, "jobTitle-link" in r2.text, len(r2.text))
        m = re.findall(r'class="[^"]*job[^"]*"', r2.text)[:8]
        print("  job classes", m)
    except Exception as e:  # noqa
        print(base, "error", e)

section("abbvie")
r = s.get("https://careers.abbvie.com/en/jobs", headers=BROWSER, timeout=30)
print("status", r.status_code, len(r.text))
print("scripts", re.findall(r'<script[^>]+src="([^"]+)"', r.text)[:15])
print("api-ish", sorted(set(re.findall(r'https?://[\w.-]+/[\w./-]*(?:api|graphql|search|jobs)[\w./?=&-]*', r.text)))[:25])
print("next_data", "__NEXT_DATA__" in r.text, "nuxt", "__NUXT__" in r.text)
i = r.text.find("__NEXT_DATA__")
if i > 0:
    print(r.text[i:i + 1500])
print("job links", re.findall(r'href="([^"]*/jobs?/[^"]+)"', r.text)[:10])

section("hmr")
for h in (UA, BROWSER):
    r = s.get("https://www.hmrlondon.com/careers", headers=h, timeout=30)
    show(r, 300)

section("quotient / psi / mac / richmond pages")
for url in ("https://www.quotientsciences.com/careers", "https://psi-cro.com/careers-filter/", "https://www.clinicalresearchjobs.co/",
            "https://richmondpharmacology.pinpointhq.com/postings.json"):
    try:
        r = s.get(url, headers=BROWSER, timeout=30)
        print(url, r.status_code, len(r.text))
        if url.endswith(".json"):
            d = r.json()
            items = d.get("data", d) if isinstance(d, dict) else d
            print("  items", [(i.get("title"), (i.get("location") or {}).get("name") if isinstance(i.get("location"), dict) else i.get("location")) for i in items][:10])
            print("  keys", list(items[0])[:30] if items else None)
            continue
        print("  iframes", re.findall(r'<iframe[^>]+src="([^"]+)"', r.text)[:5])
        links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', r.text, re.S)
        jl = [(h, re.sub(r"<[^>]+>|\s+", " ", t).strip()[:60]) for h, t in links
              if re.search(r"job|vacanc|career|position|apply|recruit|workable|teamtailor|bamboo|hirehive|pinpoint", h, re.I)]
        print("  links", jl[:25])
        if r.status_code == 202:
            print("  body", r.text[:400])
    except Exception as e:  # noqa
        print(url, "error", e)

section("radancy search (takeda, lilly, sanofi, gsk, parexel)")
for base in ("https://jobs.takeda.com", "https://careers.lilly.com", "https://jobs.sanofi.com/en", "https://jobs.gsk.com/en-gb",
             "https://jobs.parexel.com/en"):
    try:
        r = s.get(base + "/search-jobs/results", params={"ActiveFacetID": 0, "CurrentPage": 1, "RecordsPerPage": 15,
                  "Keywords": "graduate", "Location": "United Kingdom", "SearchResultsModuleName": "Search Results",
                  "SearchFiltersModuleName": "Search Filters", "SortCriteria": 0, "SortDirection": 0, "SearchType": 5},
                  headers=dict(UA, Accept="application/json", **{"X-Requested-With": "XMLHttpRequest"}), timeout=30)
        print(base, r.status_code, r.headers.get("content-type"))
        try:
            d = r.json()
            html = d.get("results", "")
            print("  hasJobs", d.get("hasJobs"), "titles", re.findall(r"<h2>(.*?)</h2>", html)[:8])
            print("  hrefs", re.findall(r'href="(/[^"]*job[^"]*)"', html)[:3])
        except Exception:
            print("  ", r.text[:300])
    except Exception as e:  # noqa
        print(base, "error", e)
