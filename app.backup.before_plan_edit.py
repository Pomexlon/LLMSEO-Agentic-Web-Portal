# app.py
import os, io, json, datetime
from pathlib import Path
from dotenv import load_dotenv

APP_DIR = Path(__file__).resolve().parent
load_dotenv(APP_DIR / ".env", override=True)
load_dotenv(APP_DIR / ".env.local", override=True)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from semrush_agent import get_domain_overview, get_domain_top_keywords
from serp_agent import run_serp_queries, run_serp_compare
from seo_audit_agent import audit_url
from llmseo_agent import draft_titles_and_meta, draft_faqs_and_schema
from kpi_scoring import compute_kpis, serp_score_from_df, combine_lvi
from pagespeed_agent import fetch_lighthouse_perf
from report_export import build_pdf

# ---------- helpers ----------
def get_secret(name: str, default: str = ""):
    try:
        return os.getenv(name) or st.secrets.get(name, default)
    except Exception:
        return os.getenv(name) or default

def data_dir_for(project: str) -> Path:
    d = (APP_DIR / "data" / (project or "default"))
    d.mkdir(parents=True, exist_ok=True)
    return d

def _gauge_color(v:int)->str:
    if v >= 75: return "#2e7d32"   # green
    if v >= 50: return "#b26a00"   # amber
    return "#c62828"               # red

def make_gauge(label:str, value:int):
    value = max(0, min(100, int(value)))
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': label, 'font': {'size':14}},
        gauge={
            'axis': {'range': [0,100]},
            'bar': {'color': _gauge_color(value)},
            'steps': [
                {'range': [0,50],  'color': '#ffe6e6'},
                {'range': [50,75], 'color': '#fff5cc'},
                {'range': [75,100],'color': '#e7f6e7'},
            ],
            'threshold': {'line': {'color': _gauge_color(value), 'width': 3}, 'thickness': 0.75, 'value': value}
        },
        number={'suffix': "%", 'font': {'size':20}}
    ))
    fig.update_layout(height=220, margin=dict(l=8,r=8,t=30,b=8))
    return fig

def render_kpi_gauges(kpi: dict, key_prefix: str = "kpi"):
    c1, c2, c3 = st.columns(3)
    c4, c5, c6 = st.columns(3)
    c1.plotly_chart(make_gauge("SERP",       kpi.get("serp_score",0)),      use_container_width=True, key=f"{key_prefix}-serp")
    c2.plotly_chart(make_gauge("Technical",  kpi.get("technical_score",0)), use_container_width=True, key=f"{key_prefix}-tech")
    c3.plotly_chart(make_gauge("Content",    kpi.get("content_score",0)),   use_container_width=True, key=f"{key_prefix}-content")
    c4.plotly_chart(make_gauge("E-E-A-T",    kpi.get("eeat_score",0)),      use_container_width=True, key=f"{key_prefix}-eeat")
    c5.plotly_chart(make_gauge("Speed",      kpi.get("speed_score",0)),     use_container_width=True, key=f"{key_prefix}-speed")
    c6.plotly_chart(make_gauge("LVI %",      kpi.get("lvi",0)),             use_container_width=True, key=f"{key_prefix}-lvi")

# ---------- UI ----------
st.set_page_config(page_title="LLMSEO Agentic Web Portal", layout="wide")
st.title("🚀 LLMSEO Agentic Web Portal")
st.caption("Enter a project, domain and keywords to run SERP, on-page audits, KPIs, LVI %, and LLM-powered recommendations.")

with st.sidebar:
    st.subheader("Environment")
    st.write("**OPENAI_API_KEY**:", "✅ set" if get_secret("OPENAI_API_KEY") else "⚠️ missing")
    st.write("**SERPAPI_KEY**:", "✅ set" if get_secret("SERPAPI_KEY") else "⚠️ missing")
    st.write("**CRAWLBASE_TOKEN**:", "✅ set" if get_secret("CRAWLBASE_TOKEN") else "—")
    st.write("**PAGESPEED_API_KEY**:", "✅ set" if get_secret("PAGESPEED_API_KEY") else "—")
    st.divider()
    st.markdown("Keep keys in `.env` locally or in **Settings → Edit secrets** on Streamlit Cloud.")
    use_crawlbase = st.checkbox("Use Crawlbase for fetching", value=bool(os.getenv("CRAWLBASE_TOKEN")))
    engine = st.selectbox("LLM engine", ["OpenAI (default)", "Claude (Anthropic)", "Grok (xAI)"], index=0)

top1, top2 = st.columns([2,1])
with top1:
    project = st.text_input("Project name (kept separate in history)", value="DemoProject")
with top2:
    location = st.selectbox("Search location", ["uk","us","de","fr","es"], index=0)

col1, col2 = st.columns([2,1])
with col1:
    domain = st.text_input("Target domain (e.g., onoxygen.co.uk)", value="")
    target_url = st.text_input("Single URL to audit (optional; leave blank to skip)")
with col2:
    st.write("")

keywords = st.text_area(
    "Keywords (one per line)",
    value="portable oxygen concentrator uk\ninogen rove 6 uk\nrefurbished oxygen concentrator uk"
)
competitors = st.text_area(
    "Competitors (optional, one per line)",
    value="theoxygenstore.com\nportableoxygen.co.uk"
)

b1, b2, b3, b4, b5, b6, b7 = st.columns(7)
run_serp = b1.button("🔎 Run SERP")
run_audit = b2.button("🧪 Run Audit")
run_plan = b3.button("🧠 Generate LLM Plan")
download_pdf = b4.button("📄 Download PDF report")
run_compare = b5.button("🏁 Compare Competitors")
semrush_enrich = b6.button("📊 SEMrush Enrich")
snapshot = b7.button("📦 One-click Snapshot")

if "serp_df" not in st.session_state: st.session_state["serp_df"] = pd.DataFrame()
if "audit_result" not in st.session_state: st.session_state["audit_result"] = {}
if "kpi" not in st.session_state: st.session_state["kpi"] = {}
if "plan" not in st.session_state: st.session_state["plan"] = {}
if "gauge_nonce" not in st.session_state: st.session_state["gauge_nonce"] = 0

# ---------- One-click Snapshot ----------
if snapshot:
    # run SERP if empty
    df = st.session_state.get("serp_df", pd.DataFrame())
    kw_list = [k.strip() for k in keywords.splitlines() if k.strip()]
    if df.empty and domain and kw_list:
        rows = run_serp_queries(domain, kw_list, gl=location)
        df = pd.DataFrame(rows)
        st.session_state["serp_df"] = df

    # run Audit if missing
    res = st.session_state.get("audit_result") or {}
    if not res and target_url:
        res = audit_url(target_url, use_crawlbase=use_crawlbase)
        st.session_state["audit_result"] = res

    # compute KPIs + PSI
    serp_score = serp_score_from_df(df, domain) if not df.empty else 50
    kpi = compute_kpis(res or {}, serp_score)
    psi_speed, field = fetch_lighthouse_perf(target_url, strategy="mobile") if target_url else (-1, {})
    if psi_speed >= 0:
        kpi["speed_score"] = psi_speed
        kpi["lvi"] = combine_lvi(kpi["serp_score"], kpi["technical_score"], kpi["content_score"], kpi["eeat_score"], kpi["speed_score"])
    st.session_state["kpi"] = kpi

    # ensure LLM Plan
    if not st.session_state.get("plan"):
        suggested = draft_titles_and_meta(
            url=target_url or f"https://{domain}",
            page_title=res.get("title",""),
            h1_count=res.get("h1_count",0),
            lvi=kpi.get("lvi",0),
            target_keywords=kw_list[:5]
        )
        faq_pack = draft_faqs_and_schema(f"{domain} oxygen", kw_list[:3] + [
            "Can I fly with a portable oxygen concentrator in the UK?",
            "Portable vs home oxygen concentrators: which is right for me?",
        ])
        st.session_state["plan"] = {
            "suggested_title": suggested.get("title",""),
            "suggested_meta": suggested.get("meta",""),
            "faqs_md": faq_pack.get("faqs_md",""),
            "faq_jsonld": faq_pack.get("faq_jsonld","")
        }

    # write history csv (per project)
    ddir = data_dir_for(project)
    hist_path = ddir / "lvi_history.csv"
    ts = datetime.datetime.utcnow().isoformat(timespec="seconds")
    row = {"timestamp": ts, "project": project, "domain": domain or "", "url": target_url, **kpi}
    if hist_path.exists():
        pd.concat([pd.read_csv(hist_path), pd.DataFrame([row])]).to_csv(hist_path, index=False)
    else:
        pd.DataFrame([row]).to_csv(hist_path, index=False)

    # Compare CSV (if ran)
    comp_path = ddir / "compare.csv"
    if not df.empty:
        # optional: keep last compare in session if you have it; else skip
        pass

    # build PDF
    serp_rows = df.to_dict("records")
    try:
        hist = pd.read_csv(hist_path)
        scope = hist[(hist["project"] == project) & (hist["domain"] == (domain or ""))].tail(10)
        hist_rows = scope.to_dict("records")
    except Exception:
        hist_rows = []
    pdf_bytes = build_pdf(project, domain, target_url, kpi, serp_rows, hist_rows, st.session_state.get("plan", {}),
                          brand_title=f"LLMSEO Visibility Report — {project or domain}",
                          logo_bytes=st.session_state.get("logo_bytes"))

    # ZIP pack
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        # artifacts in memory
        z.writestr("report.pdf", pdf_bytes)
        if not df.empty:
            z.writestr("serp_results.csv", df.to_csv(index=False))
        z.writestr("lvi_history.csv", pd.read_csv(hist_path).to_csv(index=False))
        plan_md = io.StringIO()
        p = st.session_state["plan"]
        plan_md.write(f"# Plan for {domain or target_url}\n\n**Title:** {p.get('suggested_title','')}\n\n**Meta:** {p.get('suggested_meta','')}\n\n## FAQs\n{p.get('faqs_md','')}\n\n## FAQ JSON-LD\n```json\n{p.get('faq_jsonld','')}\n```")
        z.writestr("llm_plan.md", plan_md.getvalue())

    st.download_button("⬇️ Download Snapshot (ZIP)", data=mem.getvalue(), file_name=f"{project}_snapshot.zip", mime="application/zip")
    st.success("Snapshot ready.")

# ---------- SERP ----------
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
            st.download_button("⬇️ Download SERP CSV", data=csv,
                               file_name="serp_results.csv", mime="text/csv")
# ---------- COMPARE COMPETITORS ----------
if run_compare:
    if not domain or not keywords.strip():
        st.error("Please enter a domain and at least one keyword.")
    else:
        comp_lines = [c.strip() for c in competitors.splitlines() if c.strip()]
        if not comp_lines:
            st.error("Please enter at least one competitor domain (one per line).")
        else:
            kw_list = [k.strip() for k in keywords.splitlines() if k.strip()]
            compare_rows = run_serp_compare(domain, comp_lines[:2], kw_list, gl=location)
            cdf = pd.DataFrame(compare_rows)

            st.subheader("Competitor Compare (first position in top 10)")
            st.dataframe(cdf, use_container_width=True)

            # wins/loses summary
            st.caption("Wins/Losses summary")
            wins = {"us": 0}
            for row in compare_rows:
                w = row.get("winner")
                if w == "us":
                    wins["us"] += 1
                elif w and w not in ("-", "tie") and not str(w).startswith("ERROR"):
                    wins[w] = wins.get(w, 0) + 1
            st.json(wins)

            # ✅ Download compare CSV (place it here)
            if not cdf.empty:
                csv = cdf.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download Compare CSV",
                                   data=csv,
                                   file_name="competitor_compare.csv",
                                   mime="text/csv")

# ---------- AUDIT + KPIs/LVI ----------
if run_audit:
    if not target_url:
        st.error("Enter a specific URL to audit (e.g., a product or guide page).")
    else:
        res = audit_url(target_url, use_crawlbase=use_crawlbase)
        st.session_state["audit_result"] = res

        st.subheader("On-page Audit (raw)")
        if "error" in res:
            st.error(f"Fetch error: {res['error']}")
        else:
            meta_cols = [
                "url","title","meta_description","h1_count","h2_count","img_count",
                "img_alt_coverage_percent","internal_links","external_links","jsonld_types","lvi"
            ]
            st.json({k:res.get(k) for k in meta_cols})
            st.caption("LVI breakdown (prototype subscores):")
            st.json(res.get("lvi_breakdown", {}))

            serp_df = st.session_state.get("serp_df", pd.DataFrame())
            serp_score = serp_score_from_df(serp_df, domain) if domain else 50
            kpi = compute_kpis(res, serp_score)
            st.session_state["kpi"] = kpi

            st.subheader("KPI Gauges and Overall LVI")
            st.session_state["gauge_nonce"] += 1
            render_kpi_gauges(kpi, key_prefix=f"kpi-{st.session_state['gauge_nonce']}")

            # History (per project)
            ts = datetime.datetime.utcnow().isoformat(timespec="seconds")
            ddir = data_dir_for(project)
            hist_path = ddir / "lvi_history.csv"
            row = {"timestamp": ts, "project": project, "domain": domain or "", "url": target_url, **kpi}
            if hist_path.exists():
                pd.concat([pd.read_csv(hist_path), pd.DataFrame([row])]).to_csv(hist_path, index=False)
            else:
                pd.DataFrame([row]).to_csv(hist_path, index=False)

            st.caption("Recent LVI trend (per project)")
            try:
                hist = pd.read_csv(hist_path)
                scope = hist[(hist["project"] == project) & (hist["domain"] == (domain or ""))].tail(10)
                if not scope.empty:
                    chart_df = scope[["timestamp","lvi"]].set_index("timestamp")
                    st.line_chart(chart_df, height=180)
                    st.dataframe(scope.tail(10), use_container_width=True)
            except Exception:
                pass

            # Conversions per project
            st.caption("Conversions (optional) — log weekly to show ROI")
            conv_path = ddir / "conversions.csv"
            cc1, cc2, cc3 = st.columns([1,1,2])
            with cc1:
                conv_val = st.number_input("Leads/Sales this week", min_value=0, step=1, value=0)
            with cc2:
                save_conv = st.button("Save conversions")
            if save_conv:
                conv_row = {
                    "timestamp": ts, "project": project, "domain": domain or "", "url": target_url,
                    "conversions": conv_val, "lvi": kpi["lvi"],
                }
                if conv_path.exists():
                    pd.concat([pd.read_csv(conv_path), pd.DataFrame([conv_row])]).to_csv(conv_path, index=False)
                else:
                    pd.DataFrame([conv_row]).to_csv(conv_path, index=False)
                st.success("Saved.")
            try:
                cdf = pd.read_csv(conv_path)
                cdf = cdf[(cdf["project"] == project) & (cdf["domain"] == (domain or ""))].tail(12)
                if not cdf.empty:
                    st.caption("LVI vs Conversions (last 12)")
                    st.dataframe(cdf, use_container_width=True)
                    combo = cdf[["timestamp","lvi","conversions"]].set_index("timestamp")
                    st.line_chart(combo, height=180)
            except Exception:
                pass
# ---------- SEMrush enrichment ----------
if semrush_enrich:
    try:
        st.subheader("SEMrush — Domain Overview")
        csv_text = get_domain_overview(domain or "", database=location)
        st.code(csv_text[:1200] + ("..." if len(csv_text) > 1200 else ""), language="csv")

        st.subheader("SEMrush — Top Organic Keywords")
        csv_kw = get_domain_top_keywords(domain or "", database=location, limit=25)
        st.code(csv_kw[:2000] + ("..." if len(csv_kw) > 2000 else ""), language="csv")
        st.caption("Tip: we can parse this CSV text into a DataFrame once you confirm the SEMrush plan/API units.")
    except Exception as e:
        st.error(f"SEMrush error: {e}")

# ---------- LLM Plan ----------
if run_audit:
    if not target_url:
        st.error("Enter a specific URL to audit (e.g., a product or guide page).")
    else:
        # 1) crawl + basic on-page audit
        res = audit_url(target_url)
        st.session_state["audit_result"] = res

        st.subheader("On-page Audit (raw)")
        if "error" in res:
            st.error(f"Fetch error: {res['error']}")
        else:
            meta_cols = [
                "url","title","meta_description","h1_count","h2_count","img_count",
                "img_alt_coverage_percent","internal_links","external_links","jsonld_types","lvi"
            ]
            st.json({k:res.get(k) for k in meta_cols})
            st.caption("LVI breakdown (prototype subscores):")
            st.json(res.get("lvi_breakdown", {}))

            # 2) compute KPIs (initially) using current SERP results
            serp_df = st.session_state.get("serp_df", pd.DataFrame())
            serp_score = serp_score_from_df(serp_df, domain) if domain else 50
            kpi = compute_kpis(res, serp_score)

            # 3) override Speed KPI with real PSI (PageSpeed Insights) + show field data
            psi_speed, field = fetch_lighthouse_perf(target_url, strategy="mobile")
            if psi_speed >= 0:
                kpi["speed_score"] = psi_speed
                # recompute overall LVI with new speed value
                kpi["lvi"] = combine_lvi(
                    kpi["serp_score"],
                    kpi["technical_score"],
                    kpi["content_score"],
                    kpi["eeat_score"],
                    kpi["speed_score"],
                )
                st.info(f"PageSpeed (mobile) performance: {psi_speed}")

                if field:
                    st.caption("Core Web Vitals (field data, 75th percentile)")

                    def badge(name, item):
                        cat = (item.get("category") or "").upper()
                        pct = item.get("percentile")
                        color = "#2e7d32" if cat == "GOOD" else ("#b26a00" if cat.startswith("NEEDS") else "#c62828")
                        # Pretty units for display
                        if name in ("FCP", "LCP", "INP"):
                            val = f"{int(pct)} ms" if isinstance(pct, (int, float)) else str(pct)
                        else:  # CLS
                            val = f"{pct/100:.2f}" if isinstance(pct, (int, float)) else str(pct)
                        st.markdown(
                            f"<div style='display:inline-block;padding:6px 10px;"
                            f"border-radius:8px;background:{color}20;border:1px solid {color};"
                            f"margin:4px 8px 4px 0;'>"
                            f"<b>{name}</b>: {cat} • {val}</div>",
                            unsafe_allow_html=True,
                        )

                    colA, colB = st.columns(2)
                    with colA:
                        if "FCP" in field:
                            badge("FCP", field["FCP"])
                        if "LCP" in field:
                            badge("LCP", field["LCP"])
                    with colB:
                        if "INP" in field:
                            badge("INP", field["INP"])
                        if "CLS" in field:
                            badge("CLS", field["CLS"])

                    st.caption(
                        "Good = green; Needs Improvement = amber; Poor = red. "
                        "Field data reflects real-world users."
                    )

            # 4) store KPIs in session
            st.session_state["kpi"] = kpi

            # 4) KPI gauges
            st.subheader("KPI Gauges and Overall LVI")
            render_kpi_gauges(kpi)

            # 5) save per-project history + show recent trend
            ts = datetime.datetime.utcnow().isoformat(timespec="seconds")
            ddir = data_dir_for(project)
            hist_path = ddir / "lvi_history.csv"
            row = {"timestamp": ts, "project": project, "domain": domain or "", "url": target_url, **kpi}
            if hist_path.exists():
                pd.concat([pd.read_csv(hist_path), pd.DataFrame([row])]).to_csv(hist_path, index=False)
            else:
                pd.DataFrame([row]).to_csv(hist_path, index=False)

            st.caption("Recent LVI trend (per project)")
            try:
                hist = pd.read_csv(hist_path)
                scope = hist[(hist["project"] == project) & (hist["domain"] == (domain or ""))].tail(10)
                if not scope.empty:
                    chart_df = scope[["timestamp","lvi"]].set_index("timestamp")
                    st.line_chart(chart_df, height=180)
                    st.dataframe(scope.tail(10), use_container_width=True)
            except Exception:
                pass

            # 6) conversions panel (optional, shows ROI linkage)
            st.caption("Conversions (optional) — log weekly to show ROI")
            conv_path = ddir / "conversions.csv"
            cc1, cc2, _ = st.columns([1,1,2])
            with cc1:
                conv_val = st.number_input("Leads/Sales this week", min_value=0, step=1, value=0)
            with cc2:
                save_conv = st.button("Save conversions")
            if save_conv:
                conv_row = {
                    "timestamp": ts, "project": project, "domain": domain or "", "url": target_url,
                    "conversions": conv_val, "lvi": kpi["lvi"],
                }
                if conv_path.exists():
                    pd.concat([pd.read_csv(conv_path), pd.DataFrame([conv_row])]).to_csv(conv_path, index=False)
                else:
                    pd.DataFrame([conv_row]).to_csv(conv_path, index=False)
                st.success("Saved.")
            try:
                cdf = pd.read_csv(conv_path)
                cdf = cdf[(cdf["project"] == project) & (cdf["domain"] == (domain or ""))].tail(12)
                if not cdf.empty:
                    st.caption("LVI vs Conversions (last 12)")
                    st.dataframe(cdf, use_container_width=True)
                    combo = cdf[["timestamp","lvi","conversions"]].set_index("timestamp")
                    st.line_chart(combo, height=180)
            except Exception:
                pass

# ---------- PDF Export ----------
if download_pdf:
    ddir = data_dir_for(project)
    hist_path = ddir / "lvi_history.csv"
    try:
        hist = pd.read_csv(hist_path)
        scope = hist[(hist["project"] == project) & (hist["domain"] == (domain or ""))].tail(10)
        hist_rows = scope.to_dict("records")
    except Exception:
        hist_rows = []

    serp_rows = st.session_state.get("serp_df", pd.DataFrame()).to_dict("records")
    plan = st.session_state.get("plan", {})
    kpi = st.session_state.get("kpi", {})

    pdf_bytes = build_pdf(project, domain, target_url, kpi, serp_rows, hist_rows, plan,
                          brand_title=f"LLMSEO Visibility Report — {project or domain}")
    st.download_button("⬇️ Download Branded PDF", data=pdf_bytes,
                       file_name=f"LLMSEO_{project or 'report'}.pdf", mime="application/pdf")

