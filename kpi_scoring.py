# kpi_scoring.py
"""
Turns raw audit fields into KPI scores and an overall LVI (0-100).
This is a proto; we’ll refine weights once we gather data.
"""

from typing import Dict, Tuple

WEIGHTS = {
    "serp": 25,       # (we’ll compute later when we have averages)
    "technical": 20,
    "content": 20,
    "eeat": 20,
    "speed": 15,      # placeholder until Lighthouse/PageSpeed wired
}

def clamp(n, lo, hi):
    return max(lo, min(hi, n))

def score_technical(a: Dict) -> int:
    """
    Very rough: H1 exactly 1, >=2 H2, title + meta exist, some internal links, some schema types.
    Max 100 returned; we’ll weight it later.
    """
    score = 0
    if a.get("h1_count", 0) == 1: score += 25
    if a.get("h2_count", 0) >= 2: score += 20
    if a.get("title"): score += 15
    if a.get("meta_description"): score += 10
    if a.get("internal_links", 0) >= 5: score += 15
    if len(a.get("jsonld_types", [])) >= 1: score += 15
    return clamp(score, 0, 100)

def score_content(a: Dict) -> int:
    """
    Use proxy signals: page text length via LVI breakdown’s answer_blocks, tables presence -> from audit.lvi_breakdown
    If we don’t have that breakdown, fallback to headings + images with alt coverage.
    """
    s = 0
    br = a.get("lvi_breakdown", {})
    # +15 if we saw ‘faq/q:’ style signals (audit puts 15..20)
    s += min(br.get("answer_blocks", 0), 20)
    # +10 if page has a table (specs)
    s += min(br.get("tables_specs", 0), 10)
    # alt coverage proxy
    alt_pct = a.get("img_alt_coverage_percent", 0)
    if alt_pct >= 60: s += 15
    elif alt_pct >= 30: s += 8
    # headings depth proxy
    if a.get("h2_count", 0) >= 3: s += 15
    return clamp(s, 0, 100)

def score_eeat(a: Dict) -> int:
    """Rough: audit puts 0..10 for eeat; scale to 100."""
    br = a.get("lvi_breakdown", {})
    base = br.get("eeat", 0)   # 0..10
    # add small boost if there are external links (citations)
    ext = a.get("external_links", 0)
    add = 10 if ext >= 5 else (5 if ext >= 2 else 0)
    return clamp((base * 8) + add, 0, 100)  # 10*8=80 + add

def score_speed(a: Dict) -> int:
    """
    Placeholder until PageSpeed/Lighthouse.
    Use page size proxies if we later add them; for now return a neutral 60.
    """
    return 60

def combine_lvi(serp_score: int, tech: int, content: int, eeat: int, speed: int) -> int:
    total_w = sum(WEIGHTS.values())
    weighted = (serp_score*WEIGHTS["serp"] +
                tech*WEIGHTS["technical"] +
                content*WEIGHTS["content"] +
                eeat*WEIGHTS["eeat"] +
                speed*WEIGHTS["speed"])
    return int(round(weighted / total_w))

def compute_kpis(audit_row: Dict, serp_score_hint: int = 60) -> Dict:
    """
    audit_row: the dict returned by seo_audit_agent.audit_url
    serp_score_hint: until we implement avg rank → 0..100 (higher is better).
    """
    tech = score_technical(audit_row)
    content = score_content(audit_row)
    eeat = score_eeat(audit_row)
    speed = score_speed(audit_row)

    serp = clamp(serp_score_hint, 0, 100)
    lvi = combine_lvi(serp, tech, content, eeat, speed)

    return {
        "serp_score": serp,
        "technical_score": tech,
        "content_score": content,
        "eeat_score": eeat,
        "speed_score": speed,
        "lvi": lvi,
    }

