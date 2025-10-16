# serp_agent.py
import os, time, requests
from urllib.parse import urlencode

def _get_secret(name: str):
    try:
        import streamlit as st
        return os.getenv(name) or st.secrets.get(name)
    except Exception:
        return os.getenv(name)

SERPAPI_KEY = _get_secret("SERPAPI_KEY")

def _serpapi_search(params: dict):
    if not SERPAPI_KEY:
        raise RuntimeError("SERPAPI_KEY missing. Add it to .env or Secrets")
    base = "https://serpapi.com/search.json"
    full = f"{base}?{urlencode(params)}"
    r = requests.get(full, timeout=30)
    r.raise_for_status()
    return r.json()

def run_serp_queries(domain: str, keywords: list, gl: str = "uk", hl: str = "en"):
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
# ---------- Competitor Compare ----------

def _get_secret(name: str):
    try:
        import streamlit as st
        return os.getenv(name) or st.secrets.get(name)
    except Exception:
        return os.getenv(name)

def _first_position_for_domain(organic_results: list, domain: str) -> int | None:
    if not domain:
        return None
    d = domain.lower().strip()
    for idx, item in enumerate(organic_results, start=1):
        link = (item.get("link") or "").lower()
        if d in link:
            return idx
    return None

def _top10_for_keyword(keyword: str, gl: str = "uk", hl: str = "en") -> list:
    """Return the raw top-10 organic_results list for a keyword."""
    SERPAPI_KEY = _get_secret("SERPAPI_KEY")
    if not SERPAPI_KEY:
        raise RuntimeError("SERPAPI_KEY missing. Add it to .env or Secrets")
    base = "https://serpapi.com/search.json"
    params = {
        "engine": "google",
        "q": keyword,
        "google_domain": "google.co.uk" if gl == "uk" else "google.com",
        "gl": gl,
        "hl": hl,
        "num": "10",
        "api_key": SERPAPI_KEY,
    }
    r = requests.get(base, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("organic_results", []) or []

def run_serp_compare(main_domain: str, competitors: list, keywords: list, gl: str = "uk", hl: str = "en"):
    """
    For each keyword, fetch SERP once, then compute first positions for:
      - main_domain
      - up to two competitor domains
    Returns list of rows: {keyword, our_pos, comp1_pos, comp2_pos, winner}
    """
    comps = [c.strip() for c in competitors if c.strip()]
    comp1 = comps[0] if len(comps) >= 1 else ""
    comp2 = comps[1] if len(comps) >= 2 else ""

    rows = []
    for kw in keywords:
        try:
            organic = _top10_for_keyword(kw, gl=gl, hl=hl)
            our_pos  = _first_position_for_domain(organic, main_domain)
            c1_pos   = _first_position_for_domain(organic, comp1) if comp1 else None
            c2_pos   = _first_position_for_domain(organic, comp2) if comp2 else None

            # winner logic: lowest non-None position wins; ties → "tie"
            candidates = []
            if our_pos  is not None: candidates.append(("us", our_pos))
            if c1_pos   is not None: candidates.append((comp1, c1_pos))
            if c2_pos   is not None: candidates.append((comp2, c2_pos))

            if candidates:
                best_val = min(p for _, p in candidates)
                winners = [name for name, p in candidates if p == best_val]
                winner = winners[0] if len(winners) == 1 else "tie"
            else:
                winner = "-"

            rows.append({
                "keyword": kw,
                "our_pos": our_pos,
                f"{comp1 or 'comp1'}_pos": c1_pos,
                f"{comp2 or 'comp2'}_pos": c2_pos,
                "winner": winner
            })
            time.sleep(0.6)
        except Exception as e:
            rows.append({
                "keyword": kw,
                "our_pos": None,
                f"{comp1 or 'comp1'}_pos": None,
                f"{comp2 or 'comp2'}_pos": None,
                "winner": f"ERROR: {e}"
            })
    return rows

