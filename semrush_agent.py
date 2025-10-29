# semrush_agent.py
import os, requests

SEMRUSH_API_KEY = os.getenv("SEMRUSH_API_KEY")

BASE = "https://api.semrush.com/"

def _get(params: dict):
    if not SEMRUSH_API_KEY:
        raise RuntimeError("SEMRUSH_API_KEY missing. Add it to .env or Streamlit Secrets.")
    params = {"key": SEMRUSH_API_KEY, "export": "api", **params}
    r = requests.get(BASE, params=params, timeout=45)
    r.raise_for_status()
    return r.text  # SEMrush returns CSV-like text

def get_domain_overview(domain: str, database: str = "uk"):
    # basic ranks (visibility)
    params = {"type": "domain_ranks", "domain": domain, "database": database}
    return _get(params)

def get_domain_top_keywords(domain: str, database: str = "uk", limit: int = 20):
    # top organic keywords (current positions)
    params = {"type": "domain_organic", "domain": domain, "database": database, "display_limit": str(limit)}
    return _get(params)

