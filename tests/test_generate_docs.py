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


def test_generate_marks_new_entries(monkeypatch, tmp_path):
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
        else:
            return []

    monkeypatch.setattr(generate_docs, "fetch_documents_for_dashboard", fake_fetch)

    # run generate over a small range including 59
    generate_docs.generate(dash_from=59, dash_to=116, api_key="key", keywords="foo", created_from="2026-01-01")

    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    # old entry still present, not bolded
    assert "old" in html
    assert "new" in html
    assert "<tr style=\"font-weight:bold\">" in html
    # ensure 59 was requested along with 115
    assert 59 in calls
    assert 115 in calls


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
        calls.append((did, keywords))
        return []
    monkeypatch.setattr(generate_docs, "fetch_documents_for_dashboard", fake_fetch)

    # call generate without args; defaults should use dashboard 59
    generate_docs.generate(api_key="key")
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    # default set should be in header title (cyklo, parkovani)
    assert "cyklo" in html and "parkovani" in html
    # ensure only dashboard 59 was requested and both keywords used
    kws = [kw for (_d, kw) in calls]
    assert "cyklo" in kws and "parkovani" in kws
    assert all(did == 59 for (did, _kw) in calls)


def test_generate_with_text_attachment(monkeypatch, tmp_path):
    generate_docs.OUT_DIR = str(tmp_path)
    monkeypatch.setattr(generate_docs, "fetch_dashboards", lambda key: [])
    monkeypatch.setattr(generate_docs, "filter_dashboards_by_name", lambda d, nf: [])
    # provide a document with attachment containing text
    def fake_fetch(did, api_key, keywords=None, created_from=None):
        return [{
            "edesky_id": "1",
            "created_at": "2026-03-10",
            "name": "Doc",
            "edesky_url": "u",
            "attachments": [{"name": "att", "text": "hello world"}],
        }]
    monkeypatch.setattr(generate_docs, "fetch_documents_for_dashboard", fake_fetch)

    generate_docs.generate(dash_from=59, dash_to=59, api_key="key")
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    # should include toggle button and the text in hidden row
    assert "View" in html
    assert "hello world" in html


def test_pagination_warning_display(monkeypatch, tmp_path):
    # simulate a dashboard returning multiple pages
    generate_docs.OUT_DIR = str(tmp_path)
    monkeypatch.setattr(generate_docs, "fetch_dashboards", lambda key: [])
    monkeypatch.setattr(generate_docs, "filter_dashboards_by_name", lambda d, nf: [])
    # monkeypatch client to append warning
    from aktivist_skrepr import edesky_client
    edesky_client.pagination_warnings.clear()
    def fake_fetch(did, api_key, keywords=None, created_from=None):
        # mimic client behaviour: add warning entry
        edesky_client.pagination_warnings.append((did, 3))
        return []
    monkeypatch.setattr(generate_docs, "fetch_documents_for_dashboard", fake_fetch)
    generate_docs.generate(dash_from=59, dash_to=59, api_key="key")
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "pagination disabled" in html
