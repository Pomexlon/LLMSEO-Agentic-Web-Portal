# kpi_scoring.py
from typing import Dict
import pandas as pd

WEIGHTS = {
    "serp": 25,
    "technical": 20,
    "content": 20,
    "eeat": 20,
    "speed": 15,
}

def clamp(n, lo, hi):
    return max(lo, min(hi, n))

def serp_score_from_df(df: pd.DataFrame, domain: str) -> int:
    """Convert average position of our domain into a 0–100 score."""
    if df is None or df.empty:
        return 50  # neutral if no data
    ours = df[df["our_site"] == True]
    if ours.empty:
        return 40
    avg_pos = ours["position"].mean()  # pos 1 is best
    # Simple mapping: 1 → 98-100, 5 → ~70, 10 → ~45 (clamped)
    return clamp(int(105 - avg_pos * 7), 40, 100)

def score_technical(a: Dict) -> int:
    score = 0
    if a.get("h1_count", 0) == 1: score += 25
    if a.get("h2_count", 0) >= 2: score += 20
    if a.get("title"): score += 15
    if a.get("meta_description"): score += 10
    if a.get("internal_links", 0) >= 5: score += 15
    if len(a.get("jsonld_types", [])) >= 1: score += 15
    return clamp(score, 0, 100)

def score_content(a: Dict) -> int:
    s = 0
    br = a.get("lvi_breakdown", {})
    s += min(br.get("answer_blocks", 0), 20)  # Q/A signals
    s += min(br.get("tables_specs", 0), 10)   # specs table
    alt_pct = a.get("img_alt_coverage_percent", 0)
    if alt_pct >= 60: s += 15
    elif alt_pct >= 30: s += 8
    if a.get("h2_count", 0) >= 3: s += 15
    return clamp(s, 0, 100)

def score_eeat(a: Dict) -> int:
    br = a.get("lvi_breakdown", {})
    base = br.get("eeat", 0)   # 0..10
    ext = a.get("external_links", 0)
    add = 10 if ext >= 5 else (5 if ext >= 2 else 0)
    return clamp((base * 8) + add, 0, 100)

def score_speed(a: Dict) -> int:
    return 60  # placeholder until PageSpeed/Lighthouse

def combine_lvi(serp_score: int, tech: int, content: int, eeat: int, speed: int) -> int:
    total_w = sum(WEIGHTS.values())
    weighted = (serp_score*WEIGHTS["serp"] +
                tech*WEIGHTS["technical"] +
                content*WEIGHTS["content"] +
                eeat*WEIGHTS["eeat"] +
                speed*WEIGHTS["speed"])
    return int(round(weighted / total_w))

def compute_kpis(audit_row: Dict, serp_score: int) -> Dict:
    tech = score_technical(audit_row)
    content = score_content(audit_row)
    eeat = score_eeat(audit_row)
    speed = score_speed(audit_row)
    lvi = combine_lvi(serp_score, tech, content, eeat, speed)
    return {
        "serp_score": serp_score,
        "technical_score": tech,
        "content_score": content,
        "eeat_score": eeat,
        "speed_score": speed,
        "lvi": lvi,
    }

