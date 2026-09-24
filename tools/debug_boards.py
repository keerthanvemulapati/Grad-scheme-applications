"""Temporary diagnostics for job boards that failed or under-reported. Deleted once fixed."""
import json
import re

import requests

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}
s = requests.Session()

print("===== medpace jibe =====")
base = {"lang": "en-us", "sortBy": "relevance", "descending": "false", "internal": "false"}
for extra in ({"page": 1}, {"page": 1, "limit": 100}, {"page": 1, "limit": 50}, {"page": 1, "limit": 25},
              {"page": 2}, {"page": 1, "location": "United Kingdom"}, {"page": 1, "country": "United Kingdom"},
              {"page": 1, "location": "London"}):
    r = s.get("https://careers.medpace.com/api/jobs", params=dict(base, **extra), headers=dict(UA, Accept="application/json"), timeout=30)
    try:
        d = r.json()
        jobs = d.get("jobs", [])
        print(extra, r.status_code, "total", d.get("totalCount"), "n", len(jobs),
              [(j["data"].get("title"), j["data"].get("country"), j["data"].get("city")) for j in jobs[:2]])
        if extra == {"page": 1} and jobs:
            print("  keys", sorted(jobs[0]["data"].keys())[:60])
    except Exception:
        print(extra, r.status_code, r.text[:150])

print("===== bayer eightfold =====")
for loc in ("Reading", "Reading, United Kingdom", "London, United Kingdom", "England", "GB", "Reading, England, United Kingdom"):
    r = s.get("https://talent.bayer.com/api/apply/v2/jobs", params={"domain": "bayer.com", "start": 0, "num": 10, "location": loc},
              headers=dict(UA, Accept="application/json"), timeout=30)
    d = r.json()
    print(repr(loc), "count", d.get("count"), [(p.get("name"), p.get("location")) for p in (d.get("positions") or [])[:3]])
r = s.get("https://talent.bayer.com/api/apply/v2/jobs", params={"domain": "bayer.com", "start": 400, "num": 100},
          headers=dict(UA, Accept="application/json"), timeout=30)
print("start=400", r.status_code, len((r.json().get("positions") or [])), r.json().get("count"))

print("===== ucb phenom widgets =====")
page = s.get("https://careers.ucb.com/global/en/search-results", headers=dict(UA, Accept="text/html"), timeout=30)
i = page.text.find("phApp.ddo")
ddo, _ = json.JSONDecoder().raw_decode(page.text[page.text.find("{", i):])
print("ddo keys", list(ddo)[:30])
sc = ddo.get("siteConfig") or {}
print("siteConfig", {k: sc.get(k) for k in ("lang", "country", "refNum", "locale", "siteType", "deviceType")} if sc else None)
m = re.search(r'"csrfToken"\s*:\s*"([^"]+)"', page.text)
print("csrf", bool(m))
for key in ("pageId", "pageName"):
    mm = re.search(rf'"{key}"\s*:\s*"([^"]+)"', page.text)
    print(key, mm.group(1) if mm else None)
payload = {"lang": "en_global", "deviceType": "desktop", "country": "global", "pageName": "search-results",
           "ddoKey": "refineSearch", "sortBy": "", "subsearch": "", "from": 0, "jobs": True, "counts": True,
           "all_fields": ["category", "country", "state", "city"], "size": 50, "clearAll": False,
           "jdsource": "facets", "isSliderEnable": False, "keywords": "", "global": True,
           "selected_fields": {"country": ["United Kingdom"]}, "siteType": "external"}
hdr = dict(UA, Accept="application/json", **{"Content-Type": "application/json"})
if m:
    hdr["x-csrf-token"] = m.group(1)
r = s.post("https://careers.ucb.com/widgets", json=payload, headers=hdr, timeout=30)
print("widgets", r.status_code, r.text[:300])
try:
    d = r.json().get("refineSearch", {})
    print("hits", d.get("totalHits"), [(j.get("title"), j.get("country"), j.get("city")) for j in d.get("data", {}).get("jobs", [])[:5]])
except Exception as e:  # noqa
    print("parse", e)
