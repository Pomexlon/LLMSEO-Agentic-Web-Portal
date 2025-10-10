# llmseo_agent.py
import os, json
from typing import List, Dict

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# OpenAI client (fails open to placeholder if key missing)
try:
    from openai import OpenAI
    _client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception:
    _client = None

def _fallback_titles(page_title: str):
    return {
        "title": f"{(page_title or 'Page')[:45]} | LLMSEO",
        "meta": "LLMSEO placeholder: add benefits, key specs, and a clear CTA within 155 characters."
    }

def draft_titles_and_meta(url: str, page_title: str, h1_count: int, lvi: int, target_keywords: List[str]) -> Dict[str,str]:
    """
    Suggest concise HTML <title> (<= 60 chars) and meta description (<= 155 chars).
    """
    if not _client:
        return _fallback_titles(page_title)

    prompt = f"""
You are an SEO editor. Suggest a compelling HTML <title> (<=60 chars) and meta description (<=155 chars)
for the page at {url}. Current title: "{page_title}". H1 count: {h1_count}. LVI: {lvi}.
Target keywords: {', '.join(target_keywords[:5])}.
Return JSON with keys: title, meta. No extra commentary.
"""

    try:
        r = _client.chat.completions.create(
            model=MODEL,
            messages=[{"role":"user","content":prompt}],
            temperature=0.3,
        )
        txt = (r.choices[0].message.content or "").strip()
        data = json.loads(txt) if txt.startswith("{") else {}
        return {
            "title": data.get("title") or _fallback_titles(page_title)["title"],
            "meta": data.get("meta") or _fallback_titles(page_title)["meta"]
        }
    except Exception:
        return _fallback_titles(page_title)

def draft_faqs_and_schema(topic: str, questions: List[str]) -> Dict[str, str]:
    """
    Create 4–6 Q&A pairs (80–120 words each) and a valid FAQPage JSON-LD block.
    """
    if not _client:
        # Safe placeholder if OPENAI_API_KEY not set
        faqs = [{"q": q, "a": "Add a concise, factual 80–120 word answer."} for q in questions[:5]]
        jsonld = {
            "@context":"https://schema.org",
            "@type":"FAQPage",
            "mainEntity":[{"@type":"Question","name":f["q"],"acceptedAnswer":{"@type":"Answer","text":f["a"]}} for f in faqs]
        }
        return {
            "faqs_md": "\n\n".join([f"**Q:** {f['q']}\n**A:** {f['a']}" for f in faqs]),
            "faq_jsonld": json.dumps(jsonld, indent=2)
        }

    prompt = f"""
Create 4–6 concise Q&A pairs (80–120 words each) for the topic "{topic}" with UK context where relevant.
Return strict JSON with keys:
- faqs_md: Markdown list of Q&A (use **Q:** and **A:**)
- faq_jsonld: a valid JSON string for a schema.org FAQPage (include the generated Q&A)
Questions to cover (adapt/merge if needed): {questions[:6]}
No extra commentary.
"""

    try:
        r = _client.chat.completions.create(
            model=MODEL,
            messages=[{"role":"user","content":prompt}],
            temperature=0.4,
        )
        txt = (r.choices[0].message.content or "").strip()
        data = json.loads(txt)
        return {"faqs_md": data.get("faqs_md",""), "faq_jsonld": data.get("faq_jsonld","")}
    except Exception:
        # Minimal fallback
        faqs = [{"q": q, "a": "Answer here (80–120 words)."} for q in questions[:5]]
        jsonld = {
            "@context":"https://schema.org",
            "@type":"FAQPage",
            "mainEntity":[{"@type":"Question","name":f["q"],"acceptedAnswer":{"@type":"Answer","text":f["a"]}} for f in faqs]
        }
        return {"faqs_md": "\n".join([f"**Q:** {f['q']}\n**A:** {f['a']}" for f in faqs]),
                "faq_jsonld": json.dumps(jsonld, indent=2)}

