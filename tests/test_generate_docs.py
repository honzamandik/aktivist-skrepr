import os
from datetime import datetime

import pytest

import sys, os
# ensure top-level package directories are importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts import generate_docs


def test_parse_existing_results(tmp_path):
    path = tmp_path / "index.html"
    # include timestamp and one row
    content = (
        "<html><body>generated 2024-01-01T12:00:00Z"
        "<tr><td>115</td><td>abc</td></tr></body></html>"
    )
    path.write_text(content, encoding="utf-8")
    ts, entries = generate_docs.parse_existing_results(str(path))
    assert ts is not None
    assert ts.isoformat().startswith("2024-01-01T12:00:00")
    assert entries == {(115, "abc")}


def test_generate_marks_new_entries_and_skips_59(monkeypatch, tmp_path):
    # override output directory
    generate_docs.OUT_DIR = str(tmp_path)

    # create an old HTML file with one existing entry on dashboard 115
    old_html = (
        "<html><body>generated 2024-01-10T00:00:00Z"
        "<tr><td>115</td><td>old</td></tr></body></html>"
    )
    (tmp_path / "index.html").write_text(old_html, encoding="utf-8")

    calls = []
    def fake_fetch(did, api_key, keywords=None, created_from=None):
        calls.append(did)
        if did == 115:
            return [
                {"edesky_id": "old", "created_at": "2026-01-05", "name": "a", "edesky_url": "u", "attachments": []},
                {"edesky_id": "new", "created_at": "2026-01-06", "name": "b", "edesky_url": "u2", "attachments": []},
            ]
        elif did == 116:
            return []
        elif did == 59:
            # should not be called at all
            pytest.fail("fetch_documents_for_dashboard called for skipped id 59")
        return []

    monkeypatch.setattr(generate_docs, "fetch_documents_for_dashboard", fake_fetch)

    # run generate over a small range including 59
    generate_docs.generate(dash_from=59, dash_to=116, api_key="key", keywords="foo", created_from="2026-01-01")

    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    # old entry still present, not bolded
    assert "old" in html
    assert "new" in html
    assert "<tr style=\"font-weight:bold\">" in html
    # ensure skip of 59 happened by inspecting calls
    assert 59 not in calls


def test_generate_name_filter(monkeypatch, tmp_path):
    generate_docs.OUT_DIR = str(tmp_path)
    # mimic dashboards list and filtering
    monkeypatch.setattr(generate_docs, "fetch_dashboards", lambda key: [
        {"edesky_id": "1", "name": "Praha"},
        {"edesky_id": "2", "name": "Brno"},
    ])
    monkeypatch.setattr(generate_docs, "filter_dashboards_by_name", lambda d, nf: [d[0]] if nf == "Praha" else [])

    def fake_fetch(did, api_key, keywords=None, created_from=None):
        if did == 1:
            return [{"edesky_id": "x", "created_at": "2026-02-02", "name": "t", "edesky_url": "u", "attachments": []}]
        return []
    monkeypatch.setattr(generate_docs, "fetch_documents_for_dashboard", fake_fetch)

    generate_docs.generate(api_key="key", keywords="foo", name_filter="Praha")
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "Dashboard 1 Praha" in html
    assert "x" in html


def test_generate_keywords_multiple(monkeypatch, tmp_path):
    generate_docs.OUT_DIR = str(tmp_path)
    # override dashboards to single id
    base_dash = (115, "")
    monkeypatch.setattr(generate_docs, "fetch_dashboards", lambda key: [])
    monkeypatch.setattr(generate_docs, "filter_dashboards_by_name", lambda d, nf: [])

    calls = []
    def fake_fetch(did, api_key, keywords=None, created_from=None):
        calls.append(keywords)
        if keywords == "a":
            return [{"edesky_id": "dup", "created_at": "2026-03-01", "name": "foo", "edesky_url": "u", "attachments": []}]
        if keywords == "b":
            return [{"edesky_id": "dup", "created_at": "2026-03-02", "name": "bar", "edesky_url": "u2", "attachments": []}]
        return []
    monkeypatch.setattr(generate_docs, "fetch_documents_for_dashboard", fake_fetch)

    # call generate with explicit keywords list
    generate_docs.generate(dash_from=115, dash_to=115, api_key="key", keywords="a,b")
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    # ensure both keywords were requested
    assert "a" in ''.join(calls)
    assert "b" in ''.join(calls)
    # duplicate id should only appear once in table
    assert html.count("dup") == 1
    # title should list both keywords
    assert "(a, b)" in html


def test_generate_default_keywords(monkeypatch, tmp_path):
    # ensure that omitting keywords uses built-in list
    generate_docs.OUT_DIR = str(tmp_path)
    monkeypatch.setattr(generate_docs, "fetch_dashboards", lambda key: [])
    monkeypatch.setattr(generate_docs, "filter_dashboards_by_name", lambda d, nf: [])
    calls = []
    def fake_fetch(did, api_key, keywords=None, created_from=None):
        calls.append(keywords)
        return []
    monkeypatch.setattr(generate_docs, "fetch_documents_for_dashboard", fake_fetch)

    # call generate without keywords argument
    generate_docs.generate(dash_from=115, dash_to=115, api_key="key")
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    # default set should be in header title
    assert "cyklo" in html and "opatreni" in html and "eia" in html
    # ensure fake_fetch was called with each default keyword
    for kw in ["cyklo", "opatreni", "uprava", "parkovani", "obousm", "eia"]:
        assert kw in calls
