# LLMSEO – Agentic Web Portal (V2)
# --------------------------------
# Additions from V1:
# - Branding & PDF export (company + logo uploader)
# - Nightly auto-export toggle + project snapshots + Runs list
# - Export ZIP + optional SERP enrich
# - Everything degrades gracefully if optional libs are missing

import os, json, zipfile, datetime
from textwrap import dedent
import streamlit as st

# ===== debug caption =====
try:
    st.caption(__file__)
except Exception:
    pass

# ===== optional libs (graceful fallback) =====
try:
    import requests
    from bs4 import BeautifulSoup
    HAS_SERP = True
except Exception:
    HAS_SERP = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.units import cm
    from reportlab.lib.utils import ImageReader
    from PIL import Image
    import io
    HAS_PDF = True
except Exception:
    HAS_PDF = False

# ===== constants =====
AUTO_CFG = "auto_projects.json"
PROJECTS_DIR = "projects"
EXPORTS_DIR = "exports"
PDF_DIR = os.path.join(EXPORTS_DIR, "pdf")
os.makedirs(EXPORTS_DIR, exist_ok=True)

# ===== helpers =====
def canonical_domain(domain: str) -> str:
    d = (domain or "").strip()
    for p in ("https://", "http://"):
        if d.startswith(p):
            d = d[len(p):]
    return d.strip("/")

def absolute(path: str, base_domain: str) -> str:
    if not base_domain:
        return path
    if path.startswith(("http://","https://")):
        return path
    d = canonical_domain(base_domain)
    if not path.startswith("/"):
        path = "/" + path
    return f"https://{d}{path}"

def load_auto_cfg():
    try:
        with open(AUTO_CFG, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"enabled": []}

def save_auto_cfg(cfg: dict):
    with open(AUTO_CFG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

def save_project_snapshot(project: str, domain: str, target_url: str, location: str,
                          keywords_text: str, competitors_text: str):
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    snap = {
        "project": project,
        "domain": domain,
        "target_url": target_url,
        "location": location,
        "keywords": [k.strip() for k in keywords_text.splitlines() if k.strip()],
        "competitors": [c.strip() for c in competitors_text.splitlines() if c.strip()],
        "ts": datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    }
    with open(os.path.join(PROJECTS_DIR, f"{project.replace(' ','_')}.json"), "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=2)

# ===== content generators =====
def build_seo_brief(domain: str, url: str, keywords_text: str, location: str, competitors_text: str="") -> str:
    kws = [k.strip() for k in keywords_text.splitlines() if k.strip()]
    comps = [c.strip() for c in competitors_text.splitlines() if c.strip()]
    head_kw = kws[0] if kws else "your target keyword"
    sec_kw = ", ".join(kws[1:3]) if len(kws) > 1 else ""
    comp_line = ", ".join(comps) if comps else "N/A"
    base = canonical_domain(domain) or "yourdomain"

    title = f"{head_kw.title()} | {base}"
    if len(title) > 60:
        title = f"{head_kw.title()} | {base.split('.')[0]}"

    meta = f"Compare {head_kw} options in {location.upper()} — features, pricing, and answers to common questions."
    h1 = f"{head_kw.title()} — Complete Guide ({location.upper()})"
    sections = [
        f"## What is {head_kw}?",
        "## Key Features & Benefits",
        f"## How to Choose the Right {head_kw}",
        f"## {head_kw.title()} Pricing & Availability in {location.upper()}",
        f"## {head_kw.title()} vs Alternatives",
    ]
    body = dedent(f"""
    # {h1}

    **Primary keyword:** {head_kw}  
    **Secondary keywords:** {sec_kw or "-"}  
    **Location:** {location.upper()}  
    **Competitors:** {comp_line}

    ### Page Title (<=60 chars)
    {title}

    ### Meta Description (<=160 chars)
    {meta}

    ---

    ### Suggested H2/H3 Outline
    {chr(10).join(sections)}

    ---

    ### Intro Paragraph (Draft)
    If you're researching **{head_kw}** in {location.upper()}, this guide gives you a quick overview of features, key specs to compare, and answers to common questions. Use this as a launchpad for your final page copy and on-page SEO.

    ### Section Drafts (Short)
    **What is {head_kw}?**  
    A plain-English definition, who it's for, and how it solves a problem.

    **Key Features & Benefits**  
    Bullet 3–5 genuine benefits that matter to buyers in {location.upper()}.

    **How to Choose the Right {head_kw}**  
    3–4 decision criteria: usage context, budget, maintenance, brand support.

    **Pricing & Availability**  
    Summarise ranges, typical lead times, and note key links on **{base}**.

    **{head_kw.title()} vs Alternatives**  
    Compare briefly vs 1–2 alternatives (from your competitor list if provided).

    ---

    ### Suggested FAQs (Schema-Ready)
    1. What is {head_kw} and how does it work?
    2. Is {head_kw} available in {location.upper()} and how long is delivery?
    3. How do I choose between {head_kw} and other options?
    4. What maintenance or servicing is required for {head_kw}?
    5. What are the typical costs of {head_kw} in {location.upper()}?

    ---

    ### Internal Links To Add
    - {absolute("/products", domain)}
    - {absolute("/support", domain)}
    - {absolute("/about", domain)}
    """)
    return body.strip()

def build_long_form_article(domain: str, url: str, keywords_text: str, location: str, competitors_text: str="", word_goal: int=1000) -> str:
    kws = [k.strip() for k in keywords_text.splitlines() if k.strip()]
    comps = [c.strip() for c in competitors_text.splitlines() if c.strip()]
    head_kw = kws[0] if kws else "your target keyword"
    base = canonical_domain(domain) or "yourdomain"

    intro = dedent(f"""
    # {head_kw.title()} — Complete Guide for {location.upper()}

    If you are researching **{head_kw}** in {location.upper()}, this guide covers what it is, how it works, key features, how to choose, pricing, and common questions.
    """)
    sec1 = dedent(f"## What is {head_kw}?\nExplain {head_kw} in clear language.")
    sec2 = dedent(f"## Key Features & Benefits\n- Feature #1\n- Feature #2\n- Feature #3")
    sec3 = dedent(f"## How to Choose the Right {head_kw}\nList decision criteria.")
    sec4 = dedent(f"## Pricing & Availability in {location.upper()}\nSummarise realistic ranges.")
    sec5 = dedent(f"## {head_kw.title()} vs Alternatives\nCompare to a couple of alternatives.")
    outro = dedent(f"## Next Steps\n- {absolute('/products', domain)}\n- {absolute('/contact', domain)}\n- {absolute('/reviews', domain)}")
    article = "\n\n".join([intro, sec1, sec2, sec3, sec4, sec5, outro]).strip()
    if word_goal and len(article.split()) < word_goal:
        filler = "\n\n".join([f"\n\n<!-- Expand section {i} -->" for i in range(1,6)])
        article += filler
    return article

def build_faq_pairs(keywords_text: str, location: str) -> list:
    kws = [k.strip() for k in keywords_text.splitlines() if k.strip()]
    head_kw = kws[0] if kws else "your target keyword"
    loc = location.upper()
    return [
        (f"What is {head_kw} and how does it work?", f"{head_kw.title()} is ..."),
        (f"Is {head_kw} available in {loc} and how long does delivery take?", "Typical delivery is ..."),
        (f"How do I choose the right {head_kw}?", "Compare features, usage, cost, and support."),
        (f"Do I need maintenance or servicing for {head_kw}?", "Explain basic care, servicing, warranties."),
        (f"What are typical costs of {head_kw} in {loc}?", "Give realistic ranges or how to request quotes.")
    ]

def build_faq_json_ld(domain: str, faq_pairs: list) -> str:
    items = [{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq_pairs]
    return json.dumps({"@context":"https://schema.org","@type":"FAQPage","mainEntity":items}, indent=2)

def serp_enrich(head_kw: str, location: str, max_urls: int=3, timeout: int=10) -> dict:
    if not HAS_SERP:
        return {"engine":"disabled","results":[],"error":"requests/bs4 not installed"}
    try:
        r = requests.get("https://duckduckgo.com/html/", params={"q": head_kw}, timeout=timeout, headers={"User-Agent":"Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        links = []
        for a in soup.select("a.result__a")[:max_urls]:
            href = a.get("href")
            if href and href.startswith("http"):
                links.append(href)
        results = []
        for url in links:
            try:
                pr = requests.get(url, timeout=timeout, headers={"User-Agent":"Mozilla/5.0"})
                psoup = BeautifulSoup(pr.text, "html.parser")
                h1 = psoup.find("h1").get_text(strip=True) if psoup.find("h1") else ""
                h2s = [h.get_text(strip=True) for h in psoup.find_all("h2")[:6]]
                results.append({"url": url, "h1": h1, "h2": h2s})
            except Exception:
                results.append({"url": url, "h1": "", "h2": []})
        return {"engine":"duckduckgo","results":results}
    except Exception as e:
        return {"engine":"duckduckgo","results":[],"error":str(e)}

def export_project_zip(project_name: str,
                       brief: str, keywords_text: str,
                       domain: str, target_url: str, location: str,
                       competitors_text: str,
                       serp_data: dict=None, long_form: str="",
                       faq_json_ld: str="") -> str:
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    safe_project = (project_name or "project").replace(" ", "_")
    # include location + head keyword
    head_kw = ""
    for line in (keywords_text or "").splitlines():
        if line.strip():
            head_kw = line.strip().split()[0][:15]
            break
    safe_kw = head_kw.replace(" ", "_") or "kw"
    safe_loc = (location or "loc").upper()

    zip_path = os.path.join(EXPORTS_DIR, f"{safe_project}_{safe_loc}_{safe_kw}_{ts}.zip")
    snapshot = {
        "project": project_name,
        "domain": domain,
        "target_url": target_url,
        "location": location,
        "keywords": [k.strip() for k in keywords_text.splitlines() if k.strip()],
        "competitors": [c.strip() for c in competitors_text.splitlines() if c.strip()],
        "serp": serp_data or {},
        "created_at": ts,
    }
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("seo_brief.txt", brief or "")
        zf.writestr("keywords.txt", keywords_text or "")
        zf.writestr("snapshot.json", json.dumps(snapshot, indent=2))
        if long_form:
            zf.writestr("long_form_article.md", long_form)
        if faq_json_ld:
            zf.writestr("faq_schema.jsonld", faq_json_ld)
    return zip_path
def export_pdf(brief_text: str, article_text: str, faq_json: str,
               logo_bytes: bytes, company_name: str, company_site: str,
               company_contact: str, project_name: str) -> str:
    if not HAS_PDF:
        raise RuntimeError("PDF export libraries not installed: pip install reportlab pillow")
    os.makedirs(PDF_DIR, exist_ok=True)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    safe_project = (project_name or "project").replace(" ", "_")
    pdf_path = os.path.join(PDF_DIR, f"{safe_project}_{ts}.pdf")

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
    from reportlab.lib.units import cm
    from reportlab.lib.utils import ImageReader
    import io
    from PIL import Image as PILImage

    doc = SimpleDocTemplate(pdf_path, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm, leftMargin=2*cm, rightMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    # Header: logo (scaled) + company line
    if logo_bytes:
        try:
            img = PILImage.open(io.BytesIO(logo_bytes))
            iw, ih = img.size
            maxw = 6*cm
            ratio = maxw / float(iw)
            story.append(Image(ImageReader(img), width=maxw, height=ih*ratio))
            story.append(Spacer(1, 0.5*cm))
        except Exception:
            pass

    header = f"<b>{company_name or ''}</b><br/>{company_site or ''} &nbsp;|&nbsp; {company_contact or ''}"
    story.append(Paragraph(header, styles["Normal"]))
    story.append(Spacer(1, 0.6*cm))

    # Title + time
    story.append(Paragraph(f"<b>{project_name or 'Project'}</b>", styles["Title"]))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(ts, styles["Normal"]))
    story.append(Spacer(1, 0.6*cm))

    # Mini TOC
    story.append(Paragraph("<b>Contents</b>", styles["Heading2"]))
    for t in ["1) SEO Brief", "2) Long-form Article", "3) FAQ JSON-LD"]:
        story.append(Paragraph(t, styles["Normal"]))
    story.append(Spacer(1, 0.6*cm))

    def add_section(title, txt, idx):
        if not txt:
            return
        story.append(Paragraph(f"<b>{idx}) {title}</b>", styles["Heading2"]))
        story.append(Spacer(1, 0.2*cm))
        for para in str(txt).split("\n\n"):
            story.append(Paragraph(para.replace("\n","<br/>"), styles["Normal"]))
            story.append(Spacer(1, 0.2*cm))
        story.append(Spacer(1, 0.4*cm))

    add_section("SEO Brief", brief_text, 1)
    add_section("Long-form Article", article_text, 2)
    add_section("FAQ JSON-LD", faq_json, 3)

    # Footer contact
    story.append(Spacer(1, 0.6*cm))
    story.append(Paragraph(f"{company_name or ''} &nbsp;|&nbsp; {company_site or ''} &nbsp;|&nbsp; {company_contact or ''}",
                           styles["Normal"]))

    doc.build(story)
    return pdf_path

def get_app_version():
    try:
        import subprocess
        v = subprocess.check_output(["git","rev-parse","--short","HEAD"]).decode("utf-8").strip()
        return f"Version: {v}"
    except Exception:
        return "Version: Local build"

# ===== UI =====
st.title("LLMSEO – Agentic Web Portal (V2)")
with st.expander("Projects", expanded=False):
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    proj_files = sorted([f for f in os.listdir(PROJECTS_DIR) if f.endswith(".json")])
    names = [f.replace(".json","").replace("_"," ") for f in proj_files]
    select_name = st.selectbox("Load existing project", ["(none)"] + names, index=0)
    if select_name != "(none)":
        snap = json.load(open(os.path.join(PROJECTS_DIR, f"{select_name.replace(' ','_')}.json"), "r"))
        project = snap.get("project","")
        domain = snap.get("domain","")
        target_url = snap.get("target_url","")
        location = snap.get("location","uk")
        keywords = "\n".join(snap.get("keywords", []))
        competitors = "\n".join(snap.get("competitors", []))
        st.success(f"Loaded project: {project}")

# Inputs
top1, top2 = st.columns([2,1])
with top1:
    project = st.text_input("Project name (kept separate in history)", value=st.session_state.get("project",""))
    location = st.selectbox("Search location", ["uk","us","de","fr","es"], index=0)
with top2:
    st.write("")

col1, col2 = st.columns([2,1])
with col1:
    domain = st.text_input("Target domain (e.g., example.com)", value="")
    target_url = st.text_input("Single URL to audit (optional; leave blank to skip)")
with col2:
    keywords = st.text_area("Keywords (one per line)", value="")
    competitors = st.text_area("Competitors (optional, one per line)", value="")

# Cache + snapshot
st.session_state["project"] = project
st.session_state["domain"] = domain
st.session_state["domain_cache"] = domain
st.session_state["target_url"] = target_url
st.session_state["target_url_cache"] = target_url
st.session_state["location"] = location
st.session_state["keywords_text"] = keywords
st.session_state["competitors_text"] = competitors
save_project_snapshot(project, domain, target_url, location, keywords, competitors)

# Branding & export settings
with st.expander("Branding & Export Settings", expanded=False):
    logo_file = st.file_uploader("Logo (PNG/JPG)", type=["png","jpg","jpeg"], key="logo_upload")
    company = st.text_input("Company name", st.session_state.get("company",""))
    website = st.text_input("Website URL", st.session_state.get("company_site",""))
    contact = st.text_input("Contact line (e.g., +44 1234 567890 | hello@example.com)",
                            st.session_state.get("company_contact",""))
    if logo_file:
        st.session_state["logo_bytes"] = logo_file.read()
    st.session_state["company"] = company
    st.session_state["company_site"] = website
    st.session_state["company_contact"] = contact

# Brief builder
st.markdown("---")
st.subheader("Brief Builder")
bb1, bb2 = st.columns([1,1])
with bb1:
    if st.button("📝 Generate SEO Brief", key="gen_seo_brief"):
        d, u = st.session_state.get("domain",""), st.session_state.get("target_url","")
        l = st.session_state.get("location","uk")
        kt = st.session_state.get("keywords_text","")
        ct = st.session_state.get("competitors_text","")
        if not d or not kt.strip():
            st.error("Please set a domain and at least one keyword.")
        else:
            st.session_state["last_brief"] = build_seo_brief(d, u, kt, l, ct)
with bb2:
    if "last_brief" in st.session_state:
        st.download_button("⬇️ Download Brief (TXT)",
                           data=st.session_state["last_brief"],
                           file_name="seo_brief.txt",
                           mime="text/plain")
if "last_brief" in st.session_state and st.session_state["last_brief"]:
    st.code(st.session_state["last_brief"], language="markdown")
    if st.button("💾 Save Brief to exports/", key="save_brief_btn"):
        os.makedirs(EXPORTS_DIR, exist_ok=True)
        fname = os.path.join(EXPORTS_DIR, f"brief_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt")
        with open(fname, "w", encoding="utf-8") as f:
            f.write(st.session_state["last_brief"])
        st.success(f"Saved: {fname}")

# Content & Export
st.markdown("---")
st.subheader("Content & Export")
go1, go2, go3 = st.columns([1,1,1])

with go1:
    if st.button("📝 Generate Long Article", key="gen_long_article"):
        d, u = st.session_state.get("domain",""), st.session_state.get("target_url","")
        l = st.session_state.get("location","uk")
        kt = st.session_state.get("keywords_text","")
        ct = st.session_state.get("competitors_text","")
        if not d or not kt.strip():
            st.error("Please set a domain and at least one keyword.")
        else:
            st.session_state["long_form"] = build_long_form_article(d, u, kt, l, ct)
            st.success("Long-form article draft generated.")
with go2:
    if st.button("🔎 SERP Enrich (top-3)", key="serp_enrich_btn"):
        kt = st.session_state.get("keywords_text","")
        head_kw = kt.splitlines()[0].strip() if kt.strip() else ""
        l = st.session_state.get("location", "uk")
        if not head_kw:
            st.error("Please add at least one keyword.")
        else:
            serp = serp_enrich(head_kw, l)
            st.session_state["serp_data"] = serp
            if serp.get("results"):
                st.success(f"Fetched {len(serp['results'])} result pages.")
            else:
                st.warning(f"No results or disabled (reason: {serp.get('error','n/a')}).")
with go3:
    if st.button("💬 Generate FAQ Schema", key="faq_schema_btn"):
        kt = st.session_state.get("keywords_text","")
        l = st.session_state.get("location","uk")
        pairs = build_faq_pairs(kt, l)
        st.session_state["faq_json_ld"] = build_faq_json_ld(st.session_state.get("domain",""), pairs)
        st.success("FAQ JSON-LD generated.")

if st.session_state.get("long_form",""):
    st.markdown("### Long-Form Article")
    st.code(st.session_state["long_form"], language="markdown")
    st.download_button("⬇️ Download Article (MD)",
                       data=st.session_state["long_form"],
                       file_name="long_form_article.md",
                       mime="text/markdown")

if st.session_state.get("faq_json_ld",""):
    st.markdown("### FAQ JSON-LD")
    st.code(st.session_state["faq_json_ld"], language="json")
    st.download_button("⬇️ Download FAQ Schema",
                       data=st.session_state["faq_json_ld"],
                       file_name="faq_schema.jsonld",
                       mime="application/ld+json")

# Export PDF
st.markdown("---")
if st.button("🖨️ Export PDF (branded)", key="export_pdf_btn"):
    try:
        pdf_path = export_pdf(
            brief_text=st.session_state.get("last_brief",""),
            article_text=st.session_state.get("long_form",""),
            faq_json=st.session_state.get("faq_json_ld",""),
            logo_bytes=st.session_state.get("logo_bytes", None),
            company_name=st.session_state.get("company",""),
            company_site=st.session_state.get("company_site",""),
            company_contact=st.session_state.get("company_contact",""),
            project_name=st.session_state.get("project","project")
        )
        st.success(f"PDF saved: {pdf_path}")
        with open(pdf_path, "rb") as f:
            st.download_button("⬇️ Download PDF", data=f, file_name=os.path.basename(pdf_path), mime="application/pdf")
    except Exception as e:
        st.error(f"PDF export unavailable: {e}")

# Export ZIP
if st.button("📦 Export Project (ZIP)", key="export_zip_btn"):
    zip_path = export_project_zip(
        project_name=st.session_state.get("project","project"),
        brief=st.session_state.get("last_brief",""),
        keywords_text=st.session_state.get("keywords_text",""),
        domain=st.session_state.get("domain",""),
        target_url=st.session_state.get("target_url",""),
        location=st.session_state.get("location","uk"),
        competitors_text=st.session_state.get("competitors_text",""),
        serp_data=st.session_state.get("serp_data",{}),
        long_form=st.session_state.get("long_form",""),
        faq_json_ld=st.session_state.get("faq_json_ld","")
    )
    st.success(f"Exported to {zip_path}")

# Automation (toggle + runs list)
st.markdown("---")
st.subheader("Automation")

cfg = load_auto_cfg()
enabled = set(cfg.get("enabled", []))
this_project = (st.session_state.get("project","") or "project").strip()

on = st.checkbox("Enable nightly auto-export for this project", value=this_project in enabled)
if st.button("Save automation setting"):
    if on:
        enabled.add(this_project)
    else:
        enabled.discard(this_project)
    cfg["enabled"] = sorted(list(enabled))
    save_auto_cfg(cfg)
    st.success("Saved automation configuration.")

with st.expander("Runs (exports)", expanded=False):
    files = sorted([f for f in os.listdir(EXPORTS_DIR) if os.path.isfile(os.path.join(EXPORTS_DIR,f))], reverse=True)
    if not files:
        st.write("No exports yet.")
    for fname in files[:200]:
        fpath = os.path.join(EXPORTS_DIR, fname)
        ts = datetime.datetime.fromtimestamp(os.path.getmtime(fpath)).strftime("%Y-%m-%d %H:%M")
        st.write(f"• {fname}  —  {ts}")
        with open(fpath, "rb") as f:
            st.download_button("Download", data=f, file_name=fname, mime="application/octet-stream", key=f"dl_{fname}")

# version footer
st.markdown(
    f"<div style='text-align:center; color:gray; font-size: 0.8em;'>{get_app_version()}</div>",
    unsafe_allow_html=True
)

