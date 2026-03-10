import os
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple, Optional

BASE_URL = "https://edesky.cz/api/v1/documents"
DASHBOARDS_URL = "https://edesky.cz/api/v1/dashboards"

def _build_params(keywords: str, api_key: str, dashboard_id: int, page: int = 1, created_from: Optional[str] = None) -> Dict[str, str]:
    p = {
        "keywords": keywords,
        "search_with": "sql",
        "api_key": api_key,
        "dashboard_id": str(dashboard_id),
        # use show_texts param as required by the new endpoint
        "show_texts": "1",
        "order": "date",
        "page": str(page),
        "format": "xml",
    }
    if created_from:
        p["created_from"] = created_from
    return p

def search_documents_page(dashboard_id: int, api_key: str, keywords: str = "cyklo", page: int = 1, created_from: Optional[str] = None) -> Tuple[List[Dict], int]:
    """Fetch a single page of documents for a dashboard.

    Returns (documents, total_pages).
    Each document is a dict with selected attributes.
    """
    params = _build_params(keywords, api_key, dashboard_id, page=page, created_from=created_from)
    resp = requests.get(BASE_URL, params=params, timeout=15)
    resp.raise_for_status()
    text = resp.text
    root = ET.fromstring(text)

    # page total is available as attribute on <page total='N'> or as its text
    total_pages = 1
    meta = root.find("meta")
    if meta is not None:
        page_elem = meta.find("page")
        if page_elem is not None:
            total_pages = int(page_elem.get("total") or (page_elem.text or "1"))

    docs_out: List[Dict] = []
    documents = root.find("documents")
    if documents is None:
        return docs_out, total_pages

    for doc in documents.findall("document"):
        d = dict(doc.attrib)
        # attachments (may include percent-encoded text inside element)
        atts = []
        att_block = doc.find("attachments")
        if att_block is not None:
            for a in att_block.findall("attachment"):
                att = dict(a.attrib)
                # capture any inner text and decode it
                raw = a.text or ""
                if raw:
                    from urllib.parse import unquote_plus
                    att_text = unquote_plus(raw)
                    att["text"] = att_text
                atts.append(att)
        d["attachments"] = atts
        docs_out.append(d)

    return docs_out, total_pages

# list of warnings when pagination was encountered; generator can reference this
pagination_warnings: list[tuple[int,int]] = []

def fetch_documents_for_dashboard(dashboard_id: int, api_key: str, keywords: str = "cyklo", created_from: Optional[str] = None) -> List[Dict]:
    """Fetch documents for a dashboard.

    * Only the first page is fetched; the API may return a `total` value but
      pagination is currently disabled because some tokens are not authorized.
    * Any time `total` is greater than 1 we append a warning to
      :data:`pagination_warnings` and print a message.
    """
    docs, total = search_documents_page(dashboard_id, api_key, keywords=keywords, page=1, created_from=created_from)
    if total > 1:
        pagination_warnings.append((dashboard_id, total))
        print(f"Warning: dashboard {dashboard_id} returned {total} pages; pagination disabled.")
    return docs


def fetch_dashboards(api_key: str) -> List[Dict]:
    """Retrieve the complete list of dashboards from the API.

    Returns a list of dictionaries containing attributes such as name and
    edesky_id.
    """
    params = {"api_key": api_key, "format": "xml"}
    resp = requests.get(DASHBOARDS_URL, params=params, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)

    out: List[Dict] = []
    dashes = root.find("dashboards")
    if dashes is None:
        return out
    for d in dashes.findall("dashboard"):
        out.append(dict(d.attrib))
    return out


def filter_dashboards_by_name(dashboards: List[Dict], substring: str) -> List[Dict]:
    """Return only dashboards whose "name" attribute contains substring."""
    sub = substring.lower()
    return [d for d in dashboards if sub in d.get("name", "").lower()]
