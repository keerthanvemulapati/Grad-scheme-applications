"""Temporary diagnostics for job boards that failed or under-reported. Deleted once fixed."""
import re

import requests

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}
s = requests.Session()


def section(t):
    print(f"\n===== {t} =====", flush=True)


section("abbvie filters")
r = s.get("https://careers.abbvie.com/en/jobs", headers=dict(UA, Accept="text/html"), timeout=30)
t = r.text
print("inputs", sorted(set(re.findall(r'<(?:input|select)[^>]+name="([^"]+)"', t)))[:40])
print("paging", sorted(set(re.findall(r'href="([^"]*(?:page|pg|p)=\d+[^"]*)"', t)))[:8])
print("filter links", sorted(set(re.findall(r'href="(/en/jobs\?[^"]+)"', t)))[:20])
i = t.find('/en/job/')
print("card", re.sub(r"\s+", " ", t[max(0, i - 1500):i + 1200]))
for q in ("?location=United%20Kingdom", "?country=United%20Kingdom", "?page=2", "?options=&page=2"):
    try:
        r2 = s.get("https://careers.abbvie.com/en/jobs" + q, headers=dict(UA, Accept="text/html"), timeout=30)
        ids = re.findall(r'/en/job/[^"]*?-jid-(\d+)', r2.text)
        print(q, r2.status_code, len(set(ids)), sorted(set(ids))[:5])
    except Exception as e:  # noqa
        print(q, "error", e)

section("medpace jibe variants")
for params in ({"page": 1, "lang": "en-us"}, {"page": 1, "keywords": "clinical"}, {"page": 1, "brand": "Medpace"},
               {"page": 1, "internal": "false", "userId": "", "sortBy": "relevance", "descending": "false"}):
    r = s.get("https://careers.medpace.com/api/jobs", params=params, headers=dict(UA, Accept="application/json"), timeout=30)
    try:
        print(params, r.status_code, r.json().get("totalCount"))
    except Exception:
        print(params, r.status_code, r.text[:120])

section("medpace icims raw")
r = s.get("https://international-medpace.icims.com/jobs/search", params={"pr": 0, "in_iframe": 1}, headers=UA, timeout=30)
print(r.status_code, len(r.text))
i = r.text.find("/jobs/")
print(re.sub(r"\s+", " ", r.text[max(0, i - 800):i + 1500]))

section("lilly workday en-US")
r = s.post("https://lilly.wd5.myworkdayjobs.com/wday/cxs/lilly/LLY/jobs",
           json={"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""},
           headers=dict(UA, Accept="application/json"), timeout=30)
print(r.status_code, r.text[:200])
