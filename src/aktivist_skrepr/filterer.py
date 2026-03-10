from typing import List
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def extract_links(html: str, base_url: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        links.append(urljoin(base_url, a["href"]))
    return links

def filter_links_by_keywords(links: List[str], keywords: List[str]) -> List[str]:
    lower_kw = [k.lower() for k in keywords]
    out = []
    for l in links:
        if any(k in l.lower() for k in lower_kw):
            out.append(l)
    return out
