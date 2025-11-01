# app.py   repaired  (LLMSEO portal)
import os, io, json, datetime, zipfile
from pathlib import Path
from dotenv import load_dotenv

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import subprocess
# Show the file path (helps confirm what the cloud is running)
try:
try:
    st.caption(__file__)   # shows which file the cloud is running
except Exception:
    pass

def get_app_version():
    try:
        # Try to get the short commit SHA
        version = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode("utf-8").strip()
        return f"Version: {version}"
    except Exception:
        return "Version: Local build"

# === App paths / env ===
APP_DIR = Path(__file__).resolve().parent
load_dotenv(APP_DIR / ".env", override=True)
load_dotenv(APP_DIR / ".env.local", override=True)

# === Session defaults ===
if "use_crawlbase" not in st.session_state:
    st.session_state["use_crawlbase"] = False
if "project" not in st.session_state:
    st.session_state["project"] = "DemoProject"

# === Project helpers ===
PROJECTS_DIR = (APP_DIR / "data")
PROJECTS_DIR.mkdir(exist_ok=True)

def proj_dir(name: str) -> Path:
    d = PROJECTS_DIR / (name or "default")
    d.mkdir(parents=True, exist_ok=True)
    return d

def pack_path(name: str) -> Path:
    return proj_dir(name) / "seo_pack.json"

def lvi_path(name: str) -> Path:
    return proj_dir(name) / "lvi_history.csv"

def load_pack(project: str) -> dict:
    p = pack_path(project)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return {}
    return {}

def save_pack(project: str, pack: dict) -> None:
    p = pack_path(project)
    p.write_text(json.dumps(pack, indent=2))

# === Secrets helper ===
def get_secret(name: str, default: str = ""):
    try:
        return os.getenv(name) or st.secrets.get(name, default)
    except Exception:
        return os.getenv(name) or default

# === Gauges ===
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
            'threshold': {'line': {'color': _gauge_color(value), 'width': 3},
                          'thickness': 0.75, 'value': value}
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

# === Imports for agents / helpers ===
from semrush_agent import get_domain_overview, get_domain_top_keywords
from serp_agent import run_serp_queries, run_serp_compare
from seo_audit_agent import audit_url
from llmseo_agent import draft_titles_and_meta, draft_faqs_and_schema
from kpi_scoring import compute_kpis, serp_score_from_df, combine_lvi
from pagespeed_agent import fetch_lighthouse_perf
from report_export import build_pdf
from llm_plan_helper import build_llm_plan as _build_llm_plan

# === UI: page header ===
st.set_page_config(page_title="LLMSEO Agentic Web Portal", layout="wide")
st.title(" LLMSEO Agentic Web Portal")
st.caption("Enter a project, domain and keywords to run SERP, on-page audits, KPIs, LVI %, and LLM-powered recommendations.")

# === SIDEBAR ===
with st.sidebar:
    # Environment
    st.subheader("Environment")
    st.write("**OPENAI_API_KEY**:", " set" if get_secret("OPENAI_API_KEY") else " missing")
    st.write("**SERPAPI_KEY**:", " set" if get_secret("SERPAPI_KEY") else " missing")
    st.write("**CRAWLBASE_TOKEN**:", " set" if get_secret("CRAWLBASE_TOKEN") else "")
    st.write("**PAGESPEED_API_KEY**:", " set" if get_secret("PAGESPEED_API_KEY") else "")
    st.divider()
    st.markdown("Keep keys in `.env` locally or in **Settings  Edit secrets** on Streamlit Cloud.")

    # Fetch settings
    st.markdown("### Fetch Settings")
    st.session_state["use_crawlbase"] = st.checkbox(
        "Use Crawlbase for fetching (if token present)",
        value=bool(os.getenv("CRAWLBASE_TOKEN"))
    )

    # Engine
    st.markdown("### LLM Engine")
    engine = st.selectbox("LLM engine", ["OpenAI (default)", "Claude (Anthropic)", "Grok (xAI)"], index=0)

    # Project
    st.markdown("### Project")
    existing_projects = sorted([p.name for p in PROJECTS_DIR.glob("*") if p.is_dir()])
    pick = st.selectbox("Select project", options=["<new>"] + existing_projects, index=0, key="project_select")
    new_name = st.text_input("New project name", value=st.session_state["project"], key="project_new_name")
    if st.button("Use Project", key="use_project_btn"):
        st.session_state["project"] = (new_name if pick == "<new>" else pick)
        st.success(f" Project set to: {st.session_state['project']}")

    active_project = st.session_state.get("project", "DemoProject")

    # SEO pack load/save
    st.markdown("### SEO Pack")
    uploaded_json = st.file_uploader("Upload SEO Pack (.json)", type=["json"], key="seo_pack_uploader")
    if uploaded_json is not None:
        try:
            st.session_state["seo_pack"] = json.load(uploaded_json)
            st.success(" SEO pack loaded into session")
        except Exception as e:
            st.error(f"Load error: {e}")

    cols_pack = st.columns(2)
    if cols_pack[0].button(" Save SEO Pack", key="save_pack_btn"):
        pack = st.session_state.get("seo_pack", {})
        if not pack:
            st.warning("No SEO pack in session to save.")
        else:
            save_pack(active_project, pack)
            st.success(f" Saved SEO pack under project: {active_project}")

    if cols_pack[1].button(" Load SEO Pack", key="load_pack_btn"):
        pack = load_pack(active_project)
        if pack:
            st.session_state["seo_pack"] = pack
            st.success(f" Loaded SEO pack for project: {active_project}")
        else:
            st.warning("No saved pack found for this project yet.")
st.divider()
try:
    build_env = "Cloud build" if os.getenv("STREAMLIT_RUNTIME") else "Local build"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    st.caption(f" LLMSEO Portal v1.0  {build_env} (updated {timestamp})")
except Exception as e:
    st.caption(f" LLMSEO Portal v1.0  Version info error: {e}")

    # Snapshot
    st.markdown("### LVI Snapshot")
    st.caption("Run SERP + PSI once and append to this project's history (no cron).")
    if st.button(" Run Snapshot Now", key="run_snapshot_now_btn"):
        try:
            domain_in = st.session_state.get("domain_cache", "") or st.session_state.get("domain", "")
            url_in = st.session_state.get("target_url_cache", "") or st.session_state.get("target_url", "")
            pack = st.session_state.get("seo_pack", {})
            kws = []
            if isinstance(pack.get("keywords"), list):
                kws = [k for k in pack["keywords"] if k]
            else:
                kws = [k.strip() for k in (st.session_state.get("keywords_text","")).splitlines() if k.strip()]
            if not domain_in or not kws:
                st.error("Please set a domain and at least one keyword (SEO Pack or keywords textarea).")
            else:
                rows = run_serp_queries(domain_in, kws[:5], gl="uk")
                df = pd.DataFrame(rows)
                serp_score = serp_score_from_df(df, domain_in)
                psi_score, _ = fetch_lighthouse_perf(url_in or f"https://{domain_in}", strategy="mobile")
                res = {"title": "Snapshot", "h1_count": 1}
                kpi = compute_kpis(res, serp_score)
                if psi_score >= 0:
                    kpi["speed_score"] = psi_score
                    kpi["lvi"] = combine_lvi(
                        kpi["serp_score"], kpi["technical_score"],
                        kpi["content_score"], kpi["eeat_score"], kpi["speed_score"]
                    )
                ts = datetime.datetime.utcnow().isoformat(timespec="seconds")
                row = {"timestamp": ts, "project": active_project, "domain": domain_in,
                       "url": url_in or f"https://{domain_in}", **kpi}
                hist_csv = lvi_path(active_project)
                if hist_csv.exists():
                    pd.concat([pd.read_csv(hist_csv), pd.DataFrame([row])]).to_csv(hist_csv, index=False)
                else:
                    pd.DataFrame([row]).to_csv(hist_csv, index=False)
                st.success(f" Snapshot saved to {hist_csv}")
        except Exception as e:
            st.error(f"Snapshot error: {e}")

    # Recent LVI
    st.markdown("### Recent LVI (last 10)")
    try:
        hist_csv = lvi_path(active_project)
        if hist_csv.exists():
            hist = pd.read_csv(hist_csv).tail(10)
            if not hist.empty:
                chart_df = hist[["timestamp","lvi"]].set_index("timestamp")
                st.line_chart(chart_df, height=160)
                st.dataframe(hist, use_container_width=True)
            else:
                st.info("No entries yet  run a snapshot.")
        else:
            st.info("No history file yet  run a snapshot.")
    except Exception as e:
        st.error(f"LVI panel error: {e}")
    # ---------- Project ZIP Export ----------
    st.markdown("### Project Export")
    st.caption("Bundle LVI history, conversions, SEO pack, latest SERP/Plan/PDF into a single ZIP.")
    if st.button(" Download Project ZIP", key="project_zip_export_btn"):
        try:
            active_project = st.session_state.get("project", "DemoProject")
            ddir = (APP_DIR / "data" / active_project)
            ddir.mkdir(parents=True, exist_ok=True)

            # Load saved artifacts if they exist
            hist_csv = ddir / "lvi_history.csv"
            conv_csv = ddir / "conversions.csv"
            pack_json = ddir / "seo_pack.json"

            # Prepare in-memory ZIP
            mem = io.BytesIO()
            with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:

                # LVI history
                if hist_csv.exists():
                    z.writestr("lvi_history.csv", pd.read_csv(hist_csv).to_csv(index=False))

                # Conversions
                if conv_csv.exists():
                    z.writestr("conversions.csv", pd.read_csv(conv_csv).to_csv(index=False))

                # Saved SEO pack
                if pack_json.exists():
                    z.writestr("seo_pack.json", pack_json.read_text())

                # Current SERP (from session, if any)
                serp_df = st.session_state.get("serp_df", pd.DataFrame())
                if not serp_df.empty:
                    z.writestr("serp_results.csv", serp_df.to_csv(index=False))

                # Current Plan (from session)  write as Markdown
                plan = st.session_state.get("plan", {})
                if plan:
                    md = io.StringIO()
                    md.write(f"# Plan for {st.session_state.get('domain_cache','') or st.session_state.get('target_url_cache','')}\n\n")
                    md.write(f"**Title:** {plan.get('suggested_title','')}\n\n")
                    md.write(f"**Meta:** {plan.get('suggested_meta','')}\n\n")
                    md.write("## FAQs\n")
                    md.write(plan.get("faqs_md",""))
                    md.write("\n\n## FAQ JSON-LD\n```json\n")
                    md.write(plan.get("faq_jsonld",""))
                    md.write("\n```")
                    z.writestr("llm_plan.md", md.getvalue())

                # Fresh PDF report
                try:
                    serp_rows = serp_df.to_dict("records")
                    # history rows for last 10
                    try:
                        hist = pd.read_csv(hist_csv) if hist_csv.exists() else pd.DataFrame()
                        scope = hist.tail(10) if not hist.empty else pd.DataFrame()
                        hist_rows = scope.to_dict("records")
                    except Exception:
                        hist_rows = []

                    kpi = st.session_state.get("kpi", {})
                    domain_in = st.session_state.get("domain_cache","")
                    url_in = st.session_state.get("target_url_cache","")
                    pdf_bytes = build_pdf(
                        active_project, domain_in, url_in,
                        kpi, serp_rows, hist_rows, plan,
                        brand_title=f"LLMSEO Visibility Report  {active_project}"
                    )
                    z.writestr("report.pdf", pdf_bytes)
                except Exception:
                    pass

            st.download_button("Save Project ZIP",
                               data=mem.getvalue(),
                               file_name=f"{active_project}_project_bundle.zip",
                               mime="application/zip")
        except Exception as e:
            st.error(f"Export error: {e}")

# === Main inputs ===
top1, top2 = st.columns([2,1])
with top1:
    project = st.text_input("Project name (kept separate in history)", value=st.session_state["project"])
with top2:
    location = st.selectbox("Search location", ["uk","us","de","fr","es"], index=0)

col1, col2 = st.columns([2,1])
with col1:
    domain = st.text_input("Target domain (e.g., onoxygen.co.uk)", value="")
    target_url = st.text_input("Single URL to audit (optional; leave blank to skip)")

with col2:
    st.write("")
    keywords = st.text_area("Keywords (one per line)", value="")
    st.write("")  #  adds a tiny gap
    competitors = st.text_area("Competitors (optional, one per line)", value="")

# cache for sidebar snapshot
st.session_state["project"] = project
st.session_state["domain_cache"] = domain
st.session_state["target_url_cache"] = target_url
st.session_state["keywords_text"] = keywords

# === Buttons ===
b1, b2, b3, b4, b5, b6, b7 = st.columns(7)
run_serp = b1.button(" Run SERP")
run_audit = b2.button(" Run Audit")
run_plan = b3.button(" Generate LLM Plan")
download_pdf = b4.button(" Download PDF report")
run_compare = b5.button(" Compare Competitors")
semrush_enrich = b6.button(" SEMrush Enrich")
snapshot = b7.button(" One-click Snapshot")

# === Session state inits ===
if "serp_df" not in st.session_state: st.session_state["serp_df"] = pd.DataFrame()
if "audit_result" not in st.session_state: st.session_state["audit_result"] = {}
if "kpi" not in st.session_state: st.session_state["kpi"] = {}
if "plan" not in st.session_state: st.session_state["plan"] = {}
if "gauge_nonce" not in st.session_state: st.session_state["gauge_nonce"] = 0

# === Generate LLM Plan ===
if run_plan:
    kw_list = [k.strip() for k in keywords.splitlines() if k.strip()]
    res = st.session_state.get("audit_result") or {}
    kpi = st.session_state.get("kpi", {})
    plan = _build_llm_plan(engine, domain, target_url, kw_list, res, kpi)
    st.session_state["plan"] = plan

    st.subheader("LLM Recommendations")
    st.markdown(f"**Suggested Title:** {plan.get('suggested_title','')}")
    st.markdown(f"**Meta Description:** {plan.get('suggested_meta','')}")
    st.markdown("### FAQs (Markdown)")
    st.markdown(plan.get("faqs_md","") or "_(No FAQs generated  check your engine key)_")
    st.markdown("### FAQPage JSON-LD")
    st.code(plan.get("faq_jsonld","") or "// No JSON-LD generated  check your engine key", language="json")

# === One-click Snapshot (center button) ===
if snapshot:
    df = st.session_state.get("serp_df", pd.DataFrame())
st.divider()
try:
    build_env = "Cloud build" if os.getenv("STREAMLIT_RUNTIME") else "Local build"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    st.caption(f" LLMSEO Portal v1.0  {build_env} (updated {timestamp})")
except Exception as e:
    st.caption(f" LLMSEO Portal v1.0  Version info error: {e}")
st.divider()
try:
    build_env = "Cloud build" if os.getenv("STREAMLIT_RUNTIME") else "Local build"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    st.caption(f" LLMSEO Portal v1.0  {build_env} (updated {timestamp})")
except Exception as e:
    st.caption(f" LLMSEO Portal v1.0  Version info error: {e}")
st.divider()
try:
    build_env = "Cloud build" if os.getenv("STREAMLIT_RUNTIME") else "Local build"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    st.caption(f" LLMSEO Portal v1.0  {build_env} (updated {timestamp})")
except Exception as e:
    st.caption(f" LLMSEO Portal v1.0  Version info error: {e}")
    kw_list = [k.strip() for k in keywords.splitlines() if k.strip()]
    if df.empty and domain and kw_list:
        rows = run_serp_queries(domain, kw_list, gl=location)
        df = pd.DataFrame(rows)
        st.session_state["serp_df"] = df

    res = st.session_state.get("audit_result") or {}
    if not res and target_url:
        use_cb = st.session_state.get("use_crawlbase", False)
        res = audit_url(target_url, use_crawlbase=use_cb)
        st.session_state["audit_result"] = res

    serp_score = serp_score_from_df(df, domain) if not df.empty else 50
    kpi = compute_kpis(res or {}, serp_score)
    psi_speed, _ = fetch_lighthouse_perf(target_url, strategy="mobile") if target_url else (-1, {})
    if psi_speed >= 0:
        kpi["speed_score"] = psi_speed
        kpi["lvi"] = combine_lvi(kpi["serp_score"], kpi["technical_score"], kpi["content_score"], kpi["eeat_score"], kpi["speed_score"])
    st.session_state["kpi"] = kpi

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

    ddir = proj_dir(project)
    hist_path = ddir / "lvi_history.csv"
    ts = datetime.datetime.utcnow().isoformat(timespec="seconds")
    row = {"timestamp": ts, "project": project, "domain": domain or "", "url": target_url, **kpi}
    if hist_path.exists():
        pd.concat([pd.read_csv(hist_path), pd.DataFrame([row])]).to_csv(hist_path, index=False)
    else:
        pd.DataFrame([row]).to_csv(hist_path, index=False)

    # build PDF + ZIP download
    serp_rows = df.to_dict("records")
    try:
        hist = pd.read_csv(hist_path)
        scope = hist[(hist["project"] == project) & (hist["domain"] == (domain or ""))].tail(10)
        hist_rows = scope.to_dict("records")
    except Exception:
        hist_rows = []

    pdf_bytes = build_pdf(project, domain, target_url, kpi, serp_rows, hist_rows, st.session_state.get("plan", {}),
                          brand_title=f"LLMSEO Visibility Report  {project or domain}",
                          logo_bytes=st.session_state.get("logo_bytes"))

    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("report.pdf", pdf_bytes)
        if not df.empty:
            z.writestr("serp_results.csv", df.to_csv(index=False))
        z.writestr("lvi_history.csv", pd.read_csv(hist_path).to_csv(index=False))
        p = st.session_state["plan"]
        plan_md = io.StringIO()
        plan_md.write(f"# Plan for {domain or target_url}\n\n**Title:** {p.get('suggested_title','')}\n\n**Meta:** {p.get('suggested_meta','')}\n\n## FAQs\n{p.get('faqs_md','')}\n\n## FAQ JSON-LD\n```json\n{p.get('faq_jsonld','')}\n```")
        z.writestr("llm_plan.md", plan_md.getvalue())

    st.download_button(" Download Snapshot (ZIP)", data=mem.getvalue(), file_name=f"{project}_snapshot.zip", mime="application/zip")
    st.success("Snapshot ready.")

# === SERP ===
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
            st.download_button(" Download SERP CSV", data=csv, file_name="serp_results.csv", mime="text/csv")

# === COMPARE ===
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
            st.caption("Wins/Losses summary")
            wins = {"us": 0}
            for row in compare_rows:
                w = row.get("winner")
                if w == "us": wins["us"] += 1
                elif w and w not in ("-", "tie") and not str(w).startswith("ERROR"):
                    wins[w] = wins.get(w, 0) + 1
            st.json(wins)
            if not cdf.empty:
                csv = cdf.to_csv(index=False).encode("utf-8")
                st.download_button(" Download Compare CSV", data=csv, file_name="competitor_compare.csv", mime="text/csv")

# === AUDIT + KPIs ===
if run_audit:
    if not target_url:
        st.error("Enter a specific URL to audit (e.g., a product or guide page).")
    else:
        use_cb = st.session_state.get("use_crawlbase", False)
        res = audit_url(target_url, use_crawlbase=use_cb)
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

            serp_df = st.session_state.get("serp_df", pd.DataFrame())
            serp_score = serp_score_from_df(serp_df, domain) if domain else 50
            kpi = compute_kpis(res, serp_score)
            st.session_state["kpi"] = kpi

            st.subheader("KPI Gauges and Overall LVI")
            st.session_state["gauge_nonce"] += 1
            render_kpi_gauges(kpi, key_prefix=f"kpi-{st.session_state['gauge_nonce']}")

            ts = datetime.datetime.utcnow().isoformat(timespec="seconds")
            ddir = proj_dir(project)
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

            st.caption("Conversions (optional)  log weekly to show ROI")
            conv_path = ddir / "conversions.csv"
            cc1, cc2, _ = st.columns([1,1,2])
            with cc1:
                conv_val = st.number_input("Leads/Sales this week", min_value=0, step=1, value=0, key="leads_sales_input")
            with cc2:
                save_conv = st.button("Save conversions", key="save_conversions_button_main")
            if save_conv:
                conv_row = {"timestamp": ts, "project": project, "domain": domain or "",
                            "url": target_url, "conversions": conv_val, "lvi": kpi["lvi"]}
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

# === SEMRUSH enrichment ===
if semrush_enrich:
    try:
        st.subheader("SEMrush  Domain Overview")
        csv_text = get_domain_overview(domain or "", database=location)
        st.code(csv_text[:1200] + ("..." if len(csv_text) > 1200 else ""), language="csv")

        st.subheader("SEMrush  Top Organic Keywords")
        csv_kw = get_domain_top_keywords(domain or "", database=location, limit=25)
        st.code(csv_kw[:2000] + ("..." if len(csv_kw) > 2000 else ""), language="csv")
        st.caption("Tip: we can parse this CSV text into a DataFrame once you confirm the SEMrush plan/API units.")
    except Exception as e:
        st.error(f"SEMrush error: {e}")

# === PDF export ===
if download_pdf:
    ddir = proj_dir(project)
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
                          brand_title=f"LLMSEO Visibility Report  {project or domain}")
    st.download_button(" Download Branded PDF", data=pdf_bytes,
                       file_name=f"LLMSEO_{project or 'report'}.pdf", mime="application/pdf")

st.markdown(f"<div style='text-align:center; color:gray; font-size: 0.8em;'>{get_app_version()}</div>", unsafe_allow_html=True)

