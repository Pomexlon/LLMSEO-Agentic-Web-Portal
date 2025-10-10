# serp_agent.py
import os, time, requests
from urllib.parse import urlencode

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

def _serpapi_search(params: dict):
    if not SERPAPI_KEY:
        raise RuntimeError("SERPAPI_KEY missing. Add it to .env")
    base = "https://serpapi.com/search.json"
    full = f"{base}?{urlencode(params)}"
    r = requests.get(full, timeout=30)
    r.raise_for_status()
    return r.json()

def run_serp_queries(domain: str, keywords: list, gl: str = "uk", hl: str = "en"):
    """
    For each keyword, fetch Google results and detect where the domain appears.
    Returns a list of result rows: {keyword, position, title, link, our_site}
    """
    rows = []
    for kw in keywords:
        params = {
            "engine": "google",
            "q": kw,
            "google_domain": "google.co.uk",
            "gl": gl,
            "hl": hl,
            "num": "10",
            "api_key": SERPAPI_KEY,
        }
        try:
            data = _serpapi_search(params)
            organic = data.get("organic_results", []) or []
            for idx, item in enumerate(organic, start=1):
                link = item.get("link", "")
                title = item.get("title", "")
                our_site = (domain.lower() in link.lower())
                rows.append({
                    "keyword": kw,
                    "position": idx,
                    "title": title,
                    "link": link,
                    "our_site": our_site
                })
            # Be polite with API limits
            time.sleep(0.6)
        except Exception as e:
            rows.append({
                "keyword": kw,
                "position": None,
                "title": f"ERROR: {e}",
                "link": "",
                "our_site": False
            })
    return rows

