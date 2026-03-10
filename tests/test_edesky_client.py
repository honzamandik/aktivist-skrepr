from aktivist_skrepr.edesky_client import search_documents_page, fetch_dashboards, filter_dashboards_by_name
import requests

DASHBOARD_XML = """<?xml version='1.0'?>
<edesky_search_api>
<meta><page total='2'/></meta>
<documents>
<document edesky_id='1' created_at='2026-01-01'></document>
</documents>
</edesky_search_api>
"""

DASHBOARDS_XML = """<?xml version='1.0'?>
<edesky_search_api>
<meta><dashboards_count>2</dashboards_count></meta>
<dashboards>
<dashboard edesky_id='10' name='Praha 1'/>
<dashboard edesky_id='20' name='Brno'/>
</dashboards>
</edesky_search_api>
"""


def test_search_documents_page(monkeypatch):
    class Dummy:
        text = DASHBOARD_XML
        def raise_for_status(self):
            pass
    def fake_get(url, params, timeout):
        # ensure show_texts parameter is passed
        assert params.get("show_texts") == "1"
        return Dummy()
    monkeypatch.setattr(requests, "get", fake_get)
    docs, total = search_documents_page(115, "key")
    assert total == 2
    assert len(docs) == 1
    assert docs[0]["edesky_id"] == '1'


def test_attachment_text_parsing(monkeypatch):
    # XML with attachment text encoded
    sample = """<?xml version='1.0'?><edesky_search_api><documents><document edesky_id='1'>"""
    sample += "<attachments><attachment edesky_id='a'>hello%20world</attachment></attachments>"
    sample += "</document></documents></edesky_search_api>"
    class Dummy:
        text = sample
        def raise_for_status(self):
            pass
    monkeypatch.setattr(requests, "get", lambda url, params, timeout: Dummy())
    docs, total = search_documents_page(123, "key")
    assert docs[0]['attachments'][0]['text'] == 'hello world'


def test_fetch_dashboards(monkeypatch):
    class Dummy:
        text = DASHBOARDS_XML
        def raise_for_status(self):
            pass
    monkeypatch.setattr(requests, "get", lambda url, params, timeout: Dummy())
    d = fetch_dashboards("key")
    assert isinstance(d, list)
    assert any(x["name"] == "Praha 1" for x in d)


def test_filter_dashboards_by_name():
    d = [
        {"name": "Praha 1", "edesky_id": "10"},
        {"name": "Brno", "edesky_id": "20"},
    ]
    out = filter_dashboards_by_name(d, "praha")
    assert len(out) == 1
    assert out[0]["edesky_id"] == "10"
