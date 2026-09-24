import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tracker.config import load_search  # noqa: E402


@pytest.fixture(scope="session")
def search():
    return load_search()


class FakeResponse:
    def __init__(self, payload=None, text=""):
        self._payload = payload
        self.text = text if text else (json.dumps(payload) if payload is not None else "")

    def json(self):
        return self._payload


class FakeHTTP:
    """Returns canned responses. `routes` maps a URL substring to a payload or a callable."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def _answer(self, method, url, kwargs):
        self.calls.append((method, url, kwargs))
        for key, value in self.routes.items():
            if key in url:
                value = value(method, url, kwargs) if callable(value) else value
                if isinstance(value, str):
                    return FakeResponse(text=value)
                return FakeResponse(value)
        raise AssertionError(f"Unexpected request: {method} {url}")

    def get(self, url, **kwargs):
        return self._answer("GET", url, kwargs)

    def post(self, url, **kwargs):
        return self._answer("POST", url, kwargs)
