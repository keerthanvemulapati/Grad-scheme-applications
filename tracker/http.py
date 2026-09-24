"""HTTP session with retries, timeouts and a polite delay between requests."""
from __future__ import annotations

import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0 Safari/537.36 grad-scheme-tracker/1.0"
)
TIMEOUT = 30


class PoliteSession:
    """A requests session that waits a little between calls to the same board."""

    def __init__(self, delay: float = 0.35):
        self.delay = delay
        self._last = 0.0
        self.requests_made = 0
        self.session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET", "POST"]),
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_maxsize=4)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.session.headers.update(
            {"User-Agent": USER_AGENT, "Accept-Language": "en-GB,en;q=0.9"}
        )

    def _wait(self) -> None:
        gap = time.monotonic() - self._last
        if gap < self.delay:
            time.sleep(self.delay - gap)
        self._last = time.monotonic()

    def get(self, url: str, **kwargs) -> requests.Response:
        self._wait()
        self.requests_made += 1
        kwargs.setdefault("timeout", TIMEOUT)
        resp = self.session.get(url, **kwargs)
        resp.raise_for_status()
        return resp

    def post(self, url: str, **kwargs) -> requests.Response:
        self._wait()
        self.requests_made += 1
        kwargs.setdefault("timeout", TIMEOUT)
        resp = self.session.post(url, **kwargs)
        resp.raise_for_status()
        return resp
