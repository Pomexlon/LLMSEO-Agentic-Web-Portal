# pagespeed_agent.py
import os, requests
from urllib.parse import urlencode

API_KEY = os.getenv("PAGESPEED_API_KEY", "")

def _get(url: str, strategy: str = "mobile"):
    base = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {"url": url, "strategy": strategy}
    if API_KEY:
        params["key"] = API_KEY
    r = requests.get(f"{base}?{urlencode(params)}", timeout=60)
    r.raise_for_status()
    return r.json()

def _extract_field(metrics: dict) -> dict:
    """Return a clean dict: {FCP:{category,percentile}, INP:{...}, LCP:{...}, CLS:{...}}"""
    out = {}
    mapping = {
        "FIRST_CONTENTFUL_PAINT_MS": "FCP",
        "INTERACTION_TO_NEXT_PAINT": "INP",
        "LARGEST_CONTENTFUL_PAINT_MS": "LCP",
        "CUMULATIVE_LAYOUT_SHIFT_SCORE": "CLS",
    }
    for key, short in mapping.items():
        v = metrics.get(key)
        if not v:
            continue
        out[short] = {
            "category": v.get("category"),          # GOOD / NI / POOR
            "percentile": v.get("percentile")       # ms for FCP/LCP/INP; unitless for CLS*100
        }
    return out

def fetch_lighthouse_perf(url: str, strategy: str = "mobile") -> tuple[int, dict]:
    """
    Returns (lab_score_0_100, field_data_dict).
    field_data_dict = {FCP:{category,percentile}, INP:{...}, LCP:{...}, CLS:{...}}
    If request fails, returns (-1, {}).
    """
    try:
        data = _get(url, strategy=strategy)
        # Lab score (0..1) -> 0..100
        score01 = data["lighthouseResult"]["categories"]["performance"]["score"]
        lab_score = int(round(score01 * 100))

        # Field data (user experience)
        loading = (data.get("loadingExperience") or {}).get("metrics", {})
        field = _extract_field(loading)

        # If page-level field empty, try origin-level field
        if not field:
            origin_loading = (data.get("originLoadingExperience") or {}).get("metrics", {})
            field = _extract_field(origin_loading)

        return lab_score, field
    except Exception:
        return -1, {}

