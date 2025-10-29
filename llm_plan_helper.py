# llm_plan_helper.py
def build_llm_plan(engine_label: str, domain: str, target_url: str, keywords: list, audit_row: dict, kpi: dict) -> dict:
    """
    Returns dict: {"suggested_title","suggested_meta","faqs_md","faq_jsonld"}.
    Uses OpenAI by default; switches to Claude or Grok if keys are present and engine selected.
    """
    import json
    url_for_ai = target_url or (f"https://{domain}" if domain else "")
    page_title = audit_row.get("title", "")
    h1_count = audit_row.get("h1_count", 0)
    lvi = kpi.get("lvi", audit_row.get("lvi", 0))
    kw_list = keywords[:]

    try:
        if engine_label.startswith("Claude"):
            from llm_plugins import claude_titles_and_meta, claude_faqs_and_schema
            tm = claude_titles_and_meta(url_for_ai, page_title, h1_count, lvi, kw_list)
            faq_pack = claude_faqs_and_schema(f"{domain} oxygen", kw_list[:3] + [
                "Can I fly with a portable oxygen concentrator in the UK?",
                "Portable vs home oxygen concentrators: which is right for me?",
            ])
        elif engine_label.startswith("Grok"):
            from llm_plugins import grok_titles_and_meta, grok_faqs_and_schema
            tm = grok_titles_and_meta(url_for_ai, page_title, h1_count, lvi, kw_list)
            faq_pack = grok_faqs_and_schema(f"{domain} oxygen", kw_list[:3] + [
                "Can I fly with a portable oxygen concentrator in the UK?",
                "Portable vs home oxygen concentrators: which is right for me?",
            ])
        else:
            from llmseo_agent import draft_titles_and_meta, draft_faqs_and_schema
            tm = draft_titles_and_meta(url_for_ai, page_title, h1_count, lvi, kw_list)
            faq_pack = draft_faqs_and_schema(f"{domain} oxygen", kw_list[:3] + [
                "Can I fly with a portable oxygen concentrator in the UK?",
                "Portable vs home oxygen concentrators: which is right for me?",
            ])
    except Exception:
        from llmseo_agent import draft_titles_and_meta, draft_faqs_and_schema
        tm = draft_titles_and_meta(url_for_ai, page_title, h1_count, lvi, kw_list)
        faq_pack = draft_faqs_and_schema(f"{domain} oxygen", kw_list[:3] + [
            "Can I fly with a portable oxygen concentrator in the UK?",
            "Portable vs home oxygen concentrators: which is right for me?",
        ])

    return {
        "suggested_title": tm.get("title", ""),
        "suggested_meta": tm.get("meta", ""),
        "faqs_md": faq_pack.get("faqs_md", ""),
        "faq_jsonld": faq_pack.get("faq_jsonld", "")
    }

