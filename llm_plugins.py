# llm_plugins.py
"""
Optional LLM engines for LLMSEO: Claude (Anthropic) and Grok (xAI).
If keys are not set, calls will raise RuntimeError so the app can fall back to OpenAI.
"""

import os, json, requests

# ---------- Claude (Anthropic) ----------
def claude_complete(prompt: str, max_tokens: int = 900) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY missing.")
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    model = os.getenv("CLAUDE_MODEL", "claude-3-opus-20240229")
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )
    # Anthropic returns a list of content blocks; pick the first text block
    for block in resp.content:
        if getattr(block, "type", "") == "text":
            return block.text
    return ""

def claude_titles_and_meta(url: str, page_title: str, h1_count: int, lvi: int, keywords: list) -> dict:
    prompt = f"""
You are an SEO editor. Suggest a compelling HTML <title> (<=60 chars) and meta description (<=155 chars)
for the page at {url}. Current title: "{page_title}". H1 count: {h1_count}. LVI: {lvi}.
Target keywords: {', '.join(keywords[:5])}.
Return strict JSON with keys: title, meta. No extra text.
"""
    txt = claude_complete(prompt, max_tokens=400).strip()
    try:
        return json.loads(txt)
    except Exception:
        return {"title": f"{(page_title or 'Page')[:45]} | LLMSEO", "meta": "Add benefits, key specs, and a clear CTA."}

def claude_faqs_and_schema(topic: str, questions: list) -> dict:
    prompt = f"""
Create 4–6 concise Q&A pairs (80–120 words each) for the topic "{topic}" in UK context.
Return strict JSON with keys:
- faqs_md: Markdown list (use **Q:** and **A:**)
- faq_jsonld: a valid schema.org FAQPage JSON string
Questions: {questions[:6]}
No extra commentary.
"""
    txt = claude_complete(prompt, max_tokens=1500).strip()
    try:
        data = json.loads(txt)
        return {"faqs_md": data.get("faqs_md",""), "faq_jsonld": data.get("faq_jsonld","")}
    except Exception:
        return {"faqs_md": "", "faq_jsonld": ""}

# ---------- Grok (xAI) ----------
def grok_complete(prompt: str, max_tokens: int = 900) -> str:
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        raise RuntimeError("XAI_API_KEY missing.")
    base = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
    model = os.getenv("GROK_MODEL", "grok-beta")  # adjust if your account lists a different name
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.4,
    }
    r = requests.post(f"{base}/chat/completions", headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]

def grok_titles_and_meta(url: str, page_title: str, h1_count: int, lvi: int, keywords: list) -> dict:
    prompt = f"""
You are an SEO editor. Suggest a concise HTML <title> (<=60 chars) and meta description (<=155 chars)
for the page at {url}. Current title: "{page_title}", H1 count: {h1_count}, LVI: {lvi}.
Target keywords: {', '.join(keywords[:5])}.
Return strict JSON with keys: title, meta only.
"""
    try:
        txt = grok_complete(prompt, max_tokens=500).strip()
        return json.loads(txt)
    except Exception:
        return {"title": f"{(page_title or 'Page')[:45]} | LLMSEO", "meta": "Add benefits, key specs, and a clear CTA."}

def grok_faqs_and_schema(topic: str, questions: list) -> dict:
    prompt = f"""
Create 4–6 concise Q&A pairs (80–120 words each) for the topic "{topic}" in UK context.
Output strict JSON with:
- faqs_md: Markdown with **Q:** / **A:**
- faq_jsonld: schema.org FAQPage JSON
Questions: {questions[:6]}
"""
    try:
        txt = grok_complete(prompt, max_tokens=1500).strip()
        data = json.loads(txt)
        return {"faqs_md": data.get("faqs_md",""), "faq_jsonld": data.get("faq_jsonld","")}
    except Exception:
        return {"faqs_md": "", "faq_jsonld": ""}

