import os
import pytest
from aktivist_skrepr import cli

class Dummy:
    def __init__(self, dashboard, edesky_id, created_at, name, url):
        self.attrib = {
            "dashboard": dashboard,
            "edesky_id": edesky_id,
            "created_at": created_at,
            "name": name,
            "edesky_url": url,
        }
        self.attrib = self.attrib


def test_cli_edesky_name_filter(monkeypatch, capsys):
    # Setup environment variable
    os.environ["EDESKY_API_KEY"] = "key"

    # fake dashboards list
    fake_dashboards = [{"edesky_id": "1", "name": "Praha One"}, {"edesky_id": "2", "name": "Brno"}]
    monkeypatch.setattr(cli, "fetch_dashboards", lambda api_key: fake_dashboards)

    # fake documents for id 1
    monkeypatch.setattr(cli, "fetch_documents_for_dashboard", lambda did, api_key, keywords=None, created_from=None: [
        {"edesky_id": "doc1", "created_at": "2026-01-01", "name": "Title", "edesky_url": "url", "attachments": []}
    ] if did == 1 else [])

    # capture output
    cli.main(["--edesky", "--dashboard-name-filter", "Praha"])
    captured = capsys.readouterr().out
    # keywords default should be included in header text
    assert "Edesky results" in captured
    assert "doc1" in captured


def test_cli_multiple_keywords(monkeypatch, capsys):
    os.environ["EDESKY_API_KEY"] = "key"
    # only one dashboard to simplify
    monkeypatch.setattr(cli, "fetch_dashboards", lambda api_key: [{"edesky_id": "1", "name": "Praha"}])
    # simulate different docs for each keyword and duplicate
    calls = []
    def fake_fetch(did, api_key, keywords=None, created_from=None):
        calls.append(keywords)
        if keywords == "a":
            return [{"edesky_id": "same", "created_at": "2026-01-01", "name": "Title1", "edesky_url": "url", "attachments": []}]
        if keywords == "b":
            return [{"edesky_id": "same", "created_at": "2026-01-02", "name": "Title2", "edesky_url": "url2", "attachments": []}]
        return []
    monkeypatch.setattr(cli, "fetch_documents_for_dashboard", fake_fetch)

    cli.main(["--edesky", "--dashboard-name-filter", "Praha", "--keywords", "a,b"])
    captured = capsys.readouterr().out
    # should call fetch twice, once per keyword
    assert calls.count("a") == 1
    assert calls.count("b") == 1
    # results should include only one row for the duplicate id
    assert captured.count("same") == 1
    assert "(a, b)" in captured


def test_cli_default_dashboard(monkeypatch, capsys):
    os.environ["EDESKY_API_KEY"] = "key"
    monkeypatch.setattr(cli, "fetch_dashboards", lambda api_key: [])
    calls = []
    def fake_fetch(did, api_key, keywords=None, created_from=None):
        calls.append((did, keywords))
        return []
    monkeypatch.setattr(cli, "fetch_documents_for_dashboard", fake_fetch)

    cli.main(["--edesky"])
    # two default keywords: cyklo and parkovani
    assert len(calls) == 2
    assert all(did == 59 for (did, _kw) in calls)
    captured = capsys.readouterr().out
    assert "cyklo" in captured and "parkovani" in captured
