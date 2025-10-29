# report_export.py
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from datetime import datetime

def _split_lines(text, max_len=92):
    lines, buf = [], ""
    for word in (text or "").split():
        if len(buf) + len(word) + 1 > max_len:
            lines.append(buf)
            buf = word
        else:
            buf = (buf + " " + word).strip()
    if buf: lines.append(buf)
    return lines

def build_pdf(project:str,
              domain:str,
              url:str,
              kpi:dict,
              serp_rows:list,
              history_rows:list,
              plan:dict,
              brand_title:str="LLMSEO Visibility Report",
              logo_bytes:bytes=None):
    """
    Returns PDF bytes. Keep it simple/robust for Streamlit Cloud.
    serp_rows: list of dicts (keyword, position, title, link, our_site)
    history_rows: list of dicts with at least timestamp & lvi
    """
    from io import BytesIO
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    styles = getSampleStyleSheet()
    styleH = styles["Heading1"]
    styleH2 = styles["Heading2"]
    styleN = styles["BodyText"]

    # Header
    c.setFillColor(colors.HexColor("#1f2937"))  # slate-800
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, h-2.0*cm, brand_title)
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, h-2.6*cm, f"Project: {project or '-'}   Domain: {domain or '-'}   URL: {url or '-'}")
    c.drawString(2*cm, h-3.1*cm, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

# Draw logo if provided
if logo_bytes:
    from reportlab.lib.utils import ImageReader
    try:
        img = ImageReader(io.BytesIO(logo_bytes))
        c.drawImage(img, 16.0*cm, h-3.2*cm, width=3.0*cm,
                    preserveAspectRatio=True, mask='auto')
    except Exception:
        pass

    # KPI table
    data = [
        ["SERP", "Technical", "Content", "E-E-A-T", "Speed", "LVI %"],
        [str(kpi.get("serp_score","-")),
         str(kpi.get("technical_score","-")),
         str(kpi.get("content_score","-")),
         str(kpi.get("eeat_score","-")),
         str(kpi.get("speed_score","-")),
         str(kpi.get("lvi","-"))]
    ]
    t = Table(data, colWidths=[2.5*cm]*6)
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), colors.HexColor("#e5e7eb")),
        ("TEXTCOLOR",(0,0),(-1,0), colors.HexColor("#111827")),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTNAME",(0,1),(-1,1),"Helvetica"),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("GRID",(0,0),(-1,-1), 0.4, colors.HexColor("#9ca3af")),
        ("BOTTOMPADDING",(0,0),(-1,0),6),
        ("TOPPADDING",(0,1),(-1,1),6),
    ]))
    tw, th = t.wrapOn(c, w-4*cm, h)
    t.drawOn(c, 2*cm, h-3.8*cm - th)

    y = h-3.8*cm - th - 0.7*cm

    # LVI history (last 10)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, "Recent LVI runs")
    y -= 0.5*cm

    if history_rows:
        hdr = ["timestamp","lvi"]
        rows = [[r.get("timestamp",""), str(r.get("lvi",""))] for r in history_rows[-10:]]
        hist = Table([hdr]+rows, colWidths=[7.0*cm, 2.0*cm])
        hist.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0), colors.HexColor("#e5e7eb")),
            ("GRID",(0,0),(-1,-1), 0.3, colors.HexColor("#9ca3af")),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("ALIGN",(1,1),(1,-1),"CENTER"),
        ]))
        hw, hh = hist.wrapOn(c, w-4*cm, y)
        hist.drawOn(c, 2*cm, y - hh)
        y -= hh + 0.8*cm
    else:
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(2*cm, y, "No history yet.")
        y -= 0.8*cm

    # SERP summary (first 8)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, "SERP snapshot")
    y -= 0.5*cm

    if serp_rows:
        hdr = ["kw", "pos", "title"]
        rows = []
        for r in serp_rows[:8]:
            rows.append([
                (r.get("keyword","")[:18]+"…") if len(r.get("keyword",""))>18 else r.get("keyword",""),
                str(r.get("position","")),
                (r.get("title","")[:60]+"…") if len(r.get("title",""))>60 else r.get("title","")
            ])
        serp_t = Table([hdr]+rows, colWidths=[4.0*cm, 1.5*cm, 10.0*cm])
        serp_t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0), colors.HexColor("#e5e7eb")),
            ("GRID",(0,0),(-1,-1), 0.3, colors.HexColor("#9ca3af")),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("ALIGN",(1,1),(1,-1),"CENTER"),
        ]))
        sw, sh = serp_t.wrapOn(c, w-4*cm, y)
        serp_t.drawOn(c, 2*cm, y - sh)
        y -= sh + 0.8*cm
    else:
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(2*cm, y, "No SERP results captured in this session.")
        y -= 0.8*cm

    # New page for Recommendations / FAQ
    c.showPage()
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, h-2.0*cm, "Recommendations & FAQ")

    y = h-2.7*cm
    # Title + Meta
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, "Suggested Title")
    y -= 0.45*cm
    for line in _split_lines(plan.get("suggested_title",""), 110):
        c.setFont("Helvetica", 10); c.drawString(2*cm, y, line); y -= 0.4*cm
    y -= 0.3*cm
    c.setFont("Helvetica-Bold", 12); c.drawString(2*cm, y, "Meta Description")
    y -= 0.45*cm
    for line in _split_lines(plan.get("suggested_meta",""), 110):
        c.setFont("Helvetica", 10); c.drawString(2*cm, y, line); y -= 0.4*cm
    y -= 0.5*cm

    # FAQs
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, "FAQs")
    y -= 0.5*cm
    faqs_md = plan.get("faqs_md","")
    if faqs_md:
        for raw in faqs_md.splitlines():
            line = raw.replace("**Q:**","Q:").replace("**A:**","A:")
            for l in _split_lines(line, 110):
                c.setFont("Helvetica", 10); c.drawString(2*cm, y, l); y -= 0.38*cm
                if y < 3*cm:
                    c.showPage(); y = h-2.0*cm
    else:
        c.setFont("Helvetica-Oblique", 10); c.drawString(2*cm, y, "(No FAQs generated)")
        y -= 0.5*cm

    # JSON-LD
    y -= 0.4*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, "FAQPage JSON-LD")
    y -= 0.45*cm
    jsonld = plan.get("faq_jsonld", "").strip()
    if jsonld:
        for line in _split_lines(jsonld, 100):
            c.setFont("Courier", 9)
            c.drawString(2*cm, y, line)
            y -= 0.32*cm
            if y < 2.5*cm:
                c.showPage()
                y = h - 2.0*cm
    else:
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(2*cm, y, "(No JSON-LD generated)")
        y -= 0.5*cm

    # finalize PDF and return bytes
    c.save()
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes
    
