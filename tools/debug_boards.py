"""Temporary diagnostics for job boards that failed or under-reported. Deleted once fixed."""
import re

import requests

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9", "Accept": "text/html"}
s = requests.Session()
print("===== abbvie filter variants =====")
for q in ({}, {"location-iso": "gb"}, {"location-iso": "GB", "location-name": "United Kingdom"},
          {"Content.Keyword": "regulatory"}, {"location-name": "United Kingdom", "location-iso": "gb",
                                              "location-radius": "", "location-latitude": "", "location-longitude": ""}):
    r = s.get("https://careers.abbvie.com/en/jobs", params=q, headers=UA, timeout=30)
    tiles = re.findall(r'class="attrax-vacancy-tile ([^"]+)" data-jobid="(\d+)"', r.text)
    uk = sum("united-kingdom" in c for c, _ in tiles)
    total = re.findall(r'(\d[\d,]*)\s+(?:results|jobs|vacancies)', r.text)[:3]
    print(q, r.status_code, "tiles", len(tiles), "uk", uk, "totals", total, [j for _, j in tiles][:4])
