# app.py
import os, io, json, datetime, pathlib
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import pandas as pd

from serp_agent import run_serp_queries
from seo_audit_agent import audit_url
from llmseo_agent import draft_titles_and_meta, draft_faqs_and_schema
from kpi_scoring import compute_kpis  # NEW

DATA_DIR = pathlib.Path("data")
DATA_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="LLMSEO Agentic Web Portal", layout="wide")
st.title("🚀 LLMSEO Agentic Web Portal")
st.caption("Enter a domain and keywords to run SERP, on-page audits, KPIs, LVI %, and LLM recommendations.")

with st.sidebar:
    st.subheader("Environment")
    st.write("**OPENAI_API_KEY**:", "✅ set" if os.getenv("OPENAI_API_KEY") else "⚠️ missing")
    st.write("**SERPAPI_KEY**:", "✅ set" if os.getenv("SERPAPI_KEY") else "⚠️ missing")
    st.write("**CRAWLBASE_TOKEN**:", "✅ set" if os.getenv("CRAWLBASE_TOKEN") else "—")
    st.divider()
    st.markdown("Keep keys in `.env` and **do not commit** them.")

col1, col2 = st.columns([2,1])
with col1:
    domain = st.text_input("Target domain (e.g., onoxygen.co.uk)", value="")
    target_url = st.text_input("Single URL to audit (optional; leave blank to skip)")
with col2:
    location = st.selectbox("Search location", ["uk","us","de","fr","es"], index=0)

keywords = st.text_area("Keywords (one per line)",
                        value="portable oxygen concentrator uk\ninogen rove 6 uk\nrefurbished oxygen concentrator uk")
competitors = st.text_area("Competitors (optional, one per line)",
                           value="theoxygenstore.com\nportableoxygen.co.uk")

b1, b2, b3 = st.columns(3)
run_serp = b1.button("🔎 Run SERP")
run_audit = b2.button("🧪 Run Audit")
run_plan = b3.button("🧠 Generate LLM Plan")

if "serp_df" not in st.session_state: st.session_state["serp_df"] = pd.DataFrame()
if "audit_result" not in st.session_state: st.session_state["audit_result"] = {}
if "kpi" not in st.session_state: st.session_state["kpi"] = {}
if "plan" not in st.session_state: st.session_state["plan"] = {}

# --- SERP ---
if run_serp:
    if not domain or not keywords.strip():
        st.error("Please enter a domain and at least one keyword.")
    else:
        kw_list = [k.strip() for k in keywords.splitlines() if k.strip()]
        rows = run_serp_queries(domain, kw_list, gl=location)
        df = pd.DataFrame(rows)
        st.session_state["serp_df"] = df

        st.subheader("SERP Results (Top 10 per keyword)")
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download SERP CSV", data=csv, file_name="serp_results.csv", mime="text/csv")

# Helper: derive a simple serp_score hint until we compute avg rank
def serp_score_hint(df: pd.DataFrame, domain: str) -> int:
    if df.empty: return 60
    ours = df[df["our_site"] == True]
    if ours.empty: return 40
    # Better average position => higher score (very crude)
    avg_pos = ours["position"].mean()
    return max(40, min(100, int(100 - (avg_pos-1)*8)))  # pos1->100, pos5->68, pos10->28->clamped to 40

# --- AUDIT + KPIs/LVI ---
if run_audit:
    if not target_url:
        st.error("Enter a specific URL to audit (e.g., a product or guide page).")
    else:
        res = audit_url(target_url)
        st.session_state["audit_result"] = res

        st.subheader("On-page Audit (raw)")
        if "error" in res:
            st.error(f"Fetch error: {res['error']}")
        else:
            meta_cols = ["url","title","meta_description","h1_count","h2_count","img_count",
                         "img_alt_coverage_percent","internal_links","external_links","jsonld_types","lvi"]
            st.json({k:res.get(k) for k in meta_cols})
            st.caption("LVI breakdown (prototype subscores):")
            st.json(res.get("lvi_breakdown", {}))

            # Compute KPIs + LVI
            serp_df = st.session_state.get("serp_df", pd.DataFrame())
            shp = serp_score_hint(serp_df, domain) if domain else 60
            kpi = compute_kpis(res, serp_score_hint=shp)
            st.session_state["kpi"] = kpi

            st.subheader("KPI Scores (0–100) and Overall LVI")
            kpi_df = pd.DataFrame([kpi])
            st.dataframe(kpi_df, use_container_width=True)

            # Persist a tiny history log (per site/url)
            ts = datetime.datetime.utcnow().isoformat()
            hist_path = DATA_DIR / "lvi_history.csv"
            row = {
                "timestamp": ts, "domain": domain or "", "url": target_url,
                **kpi
            }
            if hist_path.exists():
                pd.concat([pd.read_csv(hist_path), pd.DataFrame([row])]).to_csv(hist_path, index=False)
            else:
                pd.DataFrame([row]).to_csv(hist_path, index=False)

            # Show recent runs
            st.caption("Recent LVI runs")
            try:
                hist = pd.read_csv(hist_path).tail(10)
                st.dataframe(hist, use_container_width=True)
            except Exception:
                pass

# --- LLM Plan ---
if run_plan:
    if not target_url and not domain:
        st.error("Provide at least a domain or a specific URL.")
    else:
        kw_list = [k.strip() for k in keywords.splitlines() if k.strip()]
        res = st.session_state.get("audit_result") or {}

        suggested = draft_titles_and_meta(
            url=target_url or f"https://{domain}",
            page_title=res.get("title",""),
            h1_count=res.get("h1_count",0),
            lvi=st.session_state.get("kpi",{}).get("lvi", res.get("lvi",0)),
            target_keywords=kw_list[:5]
        )

        topic = f"{domain} oxygen concentrators".strip()
        qset = kw_list[:3] + [
            "Can I fly with a portable oxygen concentrator in the UK?",
            "Portable vs home oxygen concentrators: which is right for me?",
        ]
        faq_pack = draft_faqs_and_schema(topic, qset)

        plan = {
            "suggested_title": suggested.get("title",""),
            "suggested_meta": suggested.get("meta",""),
            "faqs_md": faq_pack.get("faqs_md",""),
            "faq_jsonld": faq_pack.get("faq_jsonld","")
        }
        st.session_state["plan"] = plan

        st.subheader("LLM Recommendations")
        st.markdown(f"**Suggested Title:** {plan['suggested_title']}")
        st.markdown(f"**Meta Description:** {plan['suggested_meta']}")

        st.markdown("### FAQs (Markdown)")
        st.markdown(plan["faqs_md"] or "_(No FAQs generated — check OPENAI_API_KEY)_")

        st.markdown("### FAQPage JSON-LD")
        st.code(plan["faq_jsonld"] or "// No JSON-LD generated — check OPENAI_API_KEY", language="json")

        # Download bundle
        md = io.StringIO()
        md.write(f"# LLMSEO Plan for {domain or target_url}\n\n")
        md.write(f"**Title:** {plan['suggested_title']}\n\n")
        md.write(f"**Meta:** {plan['suggested_meta']}\n\n")
        md.write("## FAQs\n")
        md.write(plan["faqs_md"])
        md.write("\n\n## FAQPage JSON-LD\n```json\n")
        md.write(plan["faq_jsonld"])
        md.write("\n```\n")
        st.download_button("⬇️ Download Plan (Markdown)",
                           md.getvalue().encode("utf-8"),
                           file_name="llmseo_plan.md", mime="text/markdown")

