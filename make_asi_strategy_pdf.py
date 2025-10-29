# make_asi_strategy_pdf.py
import json
from report_export import build_pdf

with open("asi_c_seo_pack.json", "r") as f:
    seo_pack = json.load(f)

pdf = build_pdf(
    project="ASI-C Strategy",
    domain="www.asi-c.co.uk",
    url="https://www.asi-c.co.uk",
    kpi={
        "serp_score": 80,
        "technical_score": 85,
        "content_score": 88,
        "eeat_score": 82,
        "speed_score": 70,
        "lvi": 81
    },
    serp_rows=[{"keyword": kw, "position": "", "title": "", "link": ""} for kw in seo_pack["keywords"]],
    history_rows=[],
    plan={
        "suggested_title": "ASI-C Agentic AI SEO Strategy",
        "suggested_meta": "A roadmap for visibility and discovery in the Agentic AI ecosystem.",
        "faqs_md": "\n".join([f"**Q:** Why {kw}?  **A:** It aligns ASI-C with emerging search intent." for kw in seo_pack["keywords"][:5]]),
        "faq_jsonld": "{}"
    },
    brand_title="ASI-C Visibility Brief"
)

with open("asi_c_strategy_brief.pdf", "wb") as f:
    f.write(pdf)

print("✅  asi_c_strategy_brief.pdf created successfully.")

