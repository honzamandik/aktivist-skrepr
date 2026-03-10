from aktivist_skrepr.fetcher import fetch_url
import requests

def test_fetch_url_ok(monkeypatch):
    class Dummy:
        status_code = 200
        text = "hello"
        def raise_for_status(self):
            return None

    def fake_get(url, timeout=10):
        return Dummy()

    monkeypatch.setattr(requests, "get", fake_get)
    assert fetch_url("http://example") == "hello"
