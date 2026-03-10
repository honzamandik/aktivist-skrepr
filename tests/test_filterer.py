from aktivist_skrepr.filterer import extract_links, filter_links_by_keywords

HTML = '<html><body><a href="/a">A</a><a href="https://example.com/policy">Policy</a></body></html>'

def test_extract_links():
    links = extract_links(HTML, "https://example.com")
    assert "https://example.com/a" in links

def test_filter_links_by_keywords():
    links = ["https://example.com/a", "https://example.com/policy"]
    out = filter_links_by_keywords(links, ["policy"])
    assert out == ["https://example.com/policy"]
