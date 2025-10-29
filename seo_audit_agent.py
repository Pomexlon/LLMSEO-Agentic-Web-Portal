# seo_audit_agent.py
import os, json, re, requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

CRAWLBASE_TOKEN = os.getenv("CRAWLBASE_TOKEN")

def _normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return url
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url
    return url

def _percent(n, d):
    return 0 if d == 0 else round((n/d)*100, 1)

def fetch_html(url: str, use_crawlbase: bool) -> str:
    """Fetch HTML using Crawlbase if flagged + token exists, else direct requests."""
    url = _normalize_url(url)
    if not url:
        return "__ERROR__ Missing or invalid URL"
    try:
        if use_crawlbase and CRAWLBASE_TOKEN:
            api = "https://api.crawlbase.com/"
            params = {"token": CRAWLBASE_TOKEN, "url": url, "render": "false"}
            r = requests.get(api, params=params, timeout=45)
        else:
            r = requests.get(url, timeout=45, headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
        return r.text
    except Exception as e:
        return f"__ERROR__ {e}"

def audit_url(url: str, use_crawlbase: bool = False) -> dict:
    html = fetch_html(url, use_crawlbase)
    if html.startswith("__ERROR__"):
        return {"url": _normalize_url(url), "error": html.replace("__ERROR__ ", ""), "lvi": 0}

    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.string.strip() if soup.title and soup.title.string else "")
    meta_desc = ""
    m = soup.find("meta", attrs={"name":"description"})
    if m and m.get("content"): meta_desc = m["content"].strip()

    # Headings
    h1s = [h.get_text(strip=True) for h in soup.find_all("h1")]
    h2s = [h.get_text(strip=True) for h in soup.find_all("h2")]

    # Images + alt coverage
    imgs = soup.find_all("img")
    imgs_with_alt = [i for i in imgs if i.get("alt")]
    alt_pct = _percent(len(imgs_with_alt), len(imgs))

    # Links (internal vs external)
    a_tags = soup.find_all("a", href=True)
    host = urlparse(_normalize_url(url)).netloc.lower()
    internal, external = 0, 0
    for a in a_tags:
        href = a["href"]
        if href.startswith("#"): continue
        if href.startswith(("mailto:", "tel:")): continue
        if href.startswith("/") or host in href.lower():
            internal += 1
        else:
            external += 1

    # JSON-LD presence
    ld_scripts = soup.find_all("script", type="application/ld+json")
    ld_types = []
    for s in ld_scripts:
        try:
            data = json.loads(s.string or "{}")
            if isinstance(data, dict):
                t = data.get("@type")
                if t: ld_types.append(t if isinstance(t, str) else ", ".join(t))
            elif isinstance(data, list):
                for d in data:
                    t = d.get("@type")
                    if t: ld_types.append(t if isinstance(t, str) else ", ".join(t))
        except Exception:
            pass

    # Prototype subscores (weights 0..100 total)
    score = 0
    details = {}
    sem = 0
    if len(h1s) == 1: sem += 10
    if len(h2s) >= 2: sem += 10
    score += sem; details["semantic_html"] = sem

    sch = 0
    if ld_types:
        sch = min(20, 5*len(set(ld_types)))
    score += sch; details["schema"] = sch

    ans = 0
    text = soup.get_text(" ", strip=True).lower()
    if ("faq" in text) or re.search(r"\b(q:|question:|answer:|a:)\b", text):
        ans = 15
    if len(text.split()) > 500:
        ans += 5
    score += min(ans,20); details["answer_blocks"] = min(ans,20)

    tbl = 10 if soup.find("table") else 0
    score += tbl; details["tables_specs"] = tbl

    eeat = 0
    if "last updated" in text or "date modified" in text: eeat += 5
    if re.search(r"(author|medically reviewed|reviewed by)", text): eeat += 5
    score += eeat; details["eeat"] = eeat

    il = 10 if internal >= 10 else (5 if internal >= 3 else 0)
    score += il; details["internal_links"] = il

    details["offsite"] = 0
    lvi_proto = max(0, min(100, score))

    return {
        "url": _normalize_url(url),
        "title": title,
        "meta_description": meta_desc,
        "h1_count": len(h1s),
        "h2_count": len(h2s),
        "img_count": len(imgs),
        "img_alt_coverage_percent": alt_pct,
        "internal_links": internal,
        "external_links": external,
        "jsonld_types": list(set(ld_types)),
        "lvi": lvi_proto,
        "lvi_breakdown": details
    }

