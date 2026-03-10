import requests

def fetch_url(url: str, timeout: int = 10) -> str:
    """Fetch a URL and return its text. Raises requests.HTTPError on bad status."""
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text
