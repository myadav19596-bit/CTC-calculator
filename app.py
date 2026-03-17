import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
import io, datetime

st.set_page_config(page_title="CTC Structure Generator", page_icon="💼", layout="centered")

st.markdown("""
<style>
    .block-container { max-width: 780px; padding-top: 2rem; }
    .section-title { background:#eef2f7; padding:6px 12px; border-radius:6px; font-weight:600; font-size:0.83rem; color:#555; margin:10px 0 4px 0; }
    .grand-total  { background:#dce8f7; padding:8px 14px; border-radius:6px; font-weight:600; color:#1a5fa8; margin:4px 0; }
    .net-total    { background:#d4edda; padding:8px 14px; border-radius:6px; font-weight:600; color:#2d7a3a; margin:4px 0; }
    .tmpl-selected { border:2px solid #185FA5 !important; background:#f0f6ff !important; }
</style>
""", unsafe_allow_html=True)

st.title("💼 CTC Structure Generator")
st.caption("Enter net take-home salary to auto-calculate the full CTC structure")

# ── Inputs ────────────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)
with c1:
    emp_name  = st.text_input("Employee Name",  placeholder="e.g. Rahul Sharma")
with c2:
    emp_desig = st.text_input("Designation",    placeholder="e.g. Software Engineer")

c3, c4 = st.columns(2)
with c3:
    emp_dept  = st.text_input("Department",     placeholder="e.g. Engineering")
with c4:
    emp_id    = st.text_input("Employee ID",    placeholder="e.g. EMP-001")

net_input = st.number_input(
    "Net Take-Home Salary (Monthly ₹)",
    min_value=1000, max_value=10000000, value=None,
    step=500, placeholder="e.g. 69000", format="%d"
)

# ── Template Picker ───────────────────────────────────────────────────────────
st.markdown("#### 🎨 Choose PDF Template")

TEMPLATES = {
    "original":  {"name": "Original",  "desc": "Exact match to uploaded format",      "bg": "#ffffff", "accent": "#000000"},
    "classic":   {"name": "Classic",   "desc": "Clean blue header, alternating rows",  "bg": "#1a5fa8", "accent": "#1a5fa8"},
    "modern":    {"name": "Modern",    "desc": "Dark header with teal accent",          "bg": "#1e2a3a", "accent": "#00b4a6"},
    "corporate": {"name": "Corporate", "desc": "Deep green professional style",         "bg": "#1a4731", "accent": "#2d9e6b"},
}

if "template" not in st.session_state:
    st.session_state["template"] = "original"

cols = st.columns(4)
for i, (key, tmpl) in enumerate(TEMPLATES.items()):
    with cols[i]:
        selected  = st.session_state["template"] == key
        border    = "2px solid #185FA5" if selected else "1px solid #ddd"
        bg_card   = "#f0f6ff" if selected else "transparent"
        # preview swatch
        if key == "original":
            preview_html = """<div style="background:#fff;border:1px solid #000;border-radius:4px;height:56px;display:flex;flex-direction:column;justify-content:center;padding:4px 6px;gap:3px">
              <div style="height:6px;background:#000;border-radius:1px"></div>
              <div style="height:3px;background:#ccc;border-radius:1px;width:80%"></div>
              <div style="height:3px;background:#ccc;border-radius:1px;width:60%"></div>
              <div style="height:3px;background:#ccc;border-radius:1px;width:70%"></div>
            </div>"""
        else:
            preview_html = f"""<div style="background:{tmpl['bg']};border-radius:4px;height:56px;display:flex;align-items:center;justify-content:center">
              <span style="color:#fff;font-size:9px;font-weight:700;letter-spacing:0.06em;opacity:0.9">{tmpl['name'].upper()}</span>
            </div>"""

        st.markdown(f"""
        <div style="border:{border};border-radius:10px;padding:10px;background:{bg_card}">
          {preview_html}
          <div style="font-size:12px;font-weight:600;color:{'#185FA5' if selected else '#333'};margin-top:6px">{tmpl['name']}</div>
          <div style="font-size:11px;color:#888;margin-top:2px;line-height:1.4">{tmpl['desc']}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("✓ Selected" if selected else "Select", key=f"tmpl_{key}",
                     use_container_width=True, type="primary" if selected else "secondary"):
            st.session_state["template"] = key
            st.rerun()

with st.expander("🖌️ Customise colours & font"):
    default_hdr = {"original": "#000000", "classic": "#1a5fa8", "modern": "#1e2a3a", "corporate": "#1a4731"}
    default_acc = {"original": "#000000", "classic": "#1a5fa8", "modern": "#00b4a6", "corporate": "#2d9e6b"}
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        custom_header = st.color_picker("Header / border colour", default_hdr.get(st.session_state["template"], "#1a5fa8"))
    with cc2:
        custom_accent = st.color_picker("Accent colour",          default_acc.get(st.session_state["template"], "#1a5fa8"))
    with cc3:
        custom_text   = st.color_picker("Header text colour",     "#ffffff" if st.session_state["template"] != "original" else "#000000")
    font_choice    = st.selectbox("Font", ["Times-Roman", "Helvetica", "Courier"], index=0,
                                  help="Original uses Times (Book Antiqua equivalent)")
    company_name   = st.text_input("Company name on PDF (optional)", placeholder="e.g. Acme Pvt. Ltd.")

calc_btn = st.button("🔢 Calculate CTC Structure", type="primary", use_container_width=True)


# ── Calculation ───────────────────────────────────────────────────────────────
def calc_ctc(net_monthly):
    pf_emp        = 1800
    gross         = net_monthly + pf_emp
    esic_eligible = gross < 21000
    esic_emp_amt  = round(gross * 0.0325) if esic_eligible else 0
    esic_emp_amt2 = round(gross * 0.0075) if esic_eligible else 0
    ctc           = (gross + 2300 + esic_emp_amt) / (1 - 0.02405)
    basic         = round(ctc * 0.50)
    hra           = round(basic * 0.50)
    stat_bonus    = round(basic * 0.15)
    conveyance    = gross - basic - hra - stat_bonus
    gratuity      = round(basic * 0.0481)
    health_ins    = 500
    pf_ec         = 1800
    total_gross   = basic + hra + stat_bonus + conveyance
    total_ec      = pf_ec + esic_emp_amt + gratuity + health_ins
    total_ctc     = total_gross + total_ec
    total_ded     = pf_emp + esic_emp_amt2
    net_take_home = total_gross - total_ded
    return dict(
        basic=basic, hra=hra, stat_bonus=stat_bonus, conveyance=conveyance,
        total_gross=total_gross, pf_ec=pf_ec, esic_emp_amt=esic_emp_amt,
        gratuity=gratuity, health_ins=health_ins, total_ec=total_ec,
        total_ctc=total_ctc, pf_emp=pf_emp, esic_emp_amt2=esic_emp_amt2,
        total_ded=total_ded, net_take_home=net_take_home,
        esic_eligible=esic_eligible, gross=gross
    )

def fmt(n):
    return "-" if n is None else f"₹{n:,.2f}"

def table_row(cw, label, typ, monthly, yearly, bold=False):
    cols = st.columns(cw)
    s = "**" if bold else ""
    cols[0].markdown(f"{s}{label}{s}")
    cols[1].markdown(f"<small style='color:#888'>{typ}</small>", unsafe_allow_html=True)
    cols[2].markdown(f"{s}{fmt(monthly)}{s}")
    cols[3].markdown(f"{s}{fmt(yearly)}{s}")

# ── Helper ────────────────────────────────────────────────────────────────────
def n(v):
    """Format number for PDF cell."""
    return "-" if v is None else f"{v:,.2f}"

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16)/255 for i in (0, 2, 4))


# ════════════════════════════════════════════════════════════════════════════
# ORIGINAL TEMPLATE — exact replica of uploaded PDF
# White background, black borders, Book Antiqua (Times-Roman), title at bottom
# ════════════════════════════════════════════════════════════════════════════
def pdf_original(d, name, desig, dept, eid, hdr_hex, acc_hex, txt_hex, font, company):
    buf = io.BytesIO()
    W, H = A4          # 595.27 x 841.89 pt
    M    = 36           # left/right margin
    c    = canvas.Canvas(buf, pagesize=A4)

    # Font aliases — Times-Roman closest to Book Antiqua
    B  = "Times-Roman"
    BI = "Times-Bold"
    if font != "Times-Roman":
        B  = font
        BI = font + "-Bold" if font == "Courier" else "Helvetica-Bold"

    # ── Column X positions (matching original proportions) ──────────────────
    # Original cols: Component | Type | Monthly Amt | Yearly Amt
    CX = [M,       230,   390,   490]   # left edge of each col
    CW = [194,     155,    95,    95]   # widths
    TW = W - M*2                        # total table width = 523 pt

    ROW_H    = 16    # standard row height
    HDR_H    = 18    # column header row height
    SEC_H    = 14    # section subheader row height
    y        = H - 50

    # ── Employee info block (top, if provided) ────────────────────────────
    if any([name, desig, dept, eid, company]):
        if company:
            c.setFont(BI, 11)
            c.setFillColorRGB(0, 0, 0)
            c.drawString(M, y, company)
            y -= 14
        info_parts = [x for x in [name, desig, dept, f"ID: {eid}" if eid else ""] if x]
        if info_parts:
            c.setFont(B, 9)
            c.setFillColorRGB(0.2, 0.2, 0.2)
            c.drawString(M, y, "  |  ".join(info_parts))
            y -= 14
        c.setFont(B, 8)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawRightString(W - M, y, f"Date: {datetime.date.today().strftime('%d %b %Y')}")
        y -= 16

    # ── Outer table border (drawn last via save/restore, but define rect now)
    table_top = y

    # ── Column header row ─────────────────────────────────────────────────
    # Dark background header matching original
    c.setFillColorRGB(0.15, 0.15, 0.15)
    c.rect(M, y - HDR_H + 4, TW, HDR_H, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont(BI, 9)
    c.drawString(CX[0] + 4,  y - 4, "Fixed Allowance")
    c.drawString(CX[1] + 4,  y - 4, "Type")
    c.drawRightString(CX[2] + CW[2], y - 4, "Monthly Amt")
    c.drawRightString(CX[3] + CW[3], y - 4, "Yearly Amt")
    c.setFillColorRGB(0, 0, 0)
    y -= HDR_H

    # ── Draw a table row ──────────────────────────────────────────────────
    def draw_row(label, typ, mo, yr,
                 is_section=False, is_total=False, is_grand=False, is_net=False,
                 alt=False):
        nonlocal y
        rh = SEC_H if is_section else ROW_H

        # Background fills
        if is_grand:
            c.setFillColorRGB(0.82, 0.89, 0.97)
            c.rect(M, y - rh + 4, TW, rh, fill=1, stroke=0)
        elif is_net:
            c.setFillColorRGB(0.78, 0.92, 0.80)
            c.rect(M, y - rh + 4, TW, rh, fill=1, stroke=0)
        elif is_total:
            c.setFillColorRGB(0.90, 0.90, 0.90)
            c.rect(M, y - rh + 4, TW, rh, fill=1, stroke=0)
        elif is_section:
            c.setFillColorRGB(0.94, 0.94, 0.94)
            c.rect(M, y - rh + 4, TW, rh, fill=1, stroke=0)
        elif alt:
            c.setFillColorRGB(0.97, 0.97, 0.97)
            c.rect(M, y - rh + 4, TW, rh, fill=1, stroke=0)

        # Text
        bold = is_total or is_grand or is_net or is_section
        c.setFont(BI if bold else B, 8.5 if not is_section else 8)

        if is_grand:
            c.setFillColorRGB(0.05, 0.27, 0.50)
        elif is_net:
            c.setFillColorRGB(0.08, 0.40, 0.15)
        elif is_section:
            c.setFillColorRGB(0.25, 0.25, 0.25)
        else:
            c.setFillColorRGB(0, 0, 0)

        ty = y - rh + 4 + (rh - 4) * 0.5 + 2.5   # vertically centered

        c.drawString(CX[0] + 3, ty, label)

        if not is_section:
            c.setFont(B, 7.5)
            c.setFillColorRGB(0.35, 0.35, 0.35)
            if typ:
                c.drawString(CX[1] + 3, ty, typ)
            c.setFillColorRGB(0.05, 0.27, 0.50 if is_grand else (0.08 if is_net else 0))
            if is_grand:   c.setFillColorRGB(0.05, 0.27, 0.50)
            elif is_net:   c.setFillColorRGB(0.08, 0.40, 0.15)
            else:          c.setFillColorRGB(0, 0, 0)
            c.setFont(BI if bold else B, 8.5)
            c.drawRightString(CX[2] + CW[2], ty, mo if mo else "-")
            c.drawRightString(CX[3] + CW[3], ty, yr if yr else "-")

        # Bottom border line
        c.setStrokeColorRGB(0.75, 0.75, 0.75)
        c.setLineWidth(0.4)
        c.line(M, y - rh + 4, M + TW, y - rh + 4)

        y -= rh

    # ── Draw all rows ─────────────────────────────────────────────────────
    alt = False
    draw_row("Basic Salary",                    "Fully Taxable",                  n(d["basic"]),      n(d["basic"]*12),      alt=alt); alt=not alt
    draw_row("House Rent Allowance",            "Fully Taxable",                  n(d["hra"]),         n(d["hra"]*12),        alt=alt); alt=not alt
    draw_row("Statutory Bonus",                 "Fully Taxable",                  n(d["stat_bonus"]),  n(d["stat_bonus"]*12), alt=alt); alt=not alt
    draw_row("Conveyance/ Transport Allowance", "Fully Taxable",                  n(d["conveyance"]),  n(d["conveyance"]*12), alt=alt); alt=not alt
    draw_row("Total Gross Salary (A)",          "",                               n(d["total_gross"]), n(d["total_gross"]*12),is_total=True)

    draw_row("Employer Contributions & Perquisites", "", None, None,              is_section=True); alt=False
    draw_row("PF employer contribution",        "Employer rate 12% of 15000",     n(d["pf_ec"]),       n(d["pf_ec"]*12),      alt=alt); alt=not alt
    draw_row("ESIC employer contribution",
             "Employer rate 3.25%" if d["esic_eligible"] else "Employer rate 3.25%",
             n(d["esic_emp_amt"]) if d["esic_eligible"] else "-",
             n(d["esic_emp_amt"]*12) if d["esic_eligible"] else "-",             alt=alt); alt=not alt
    draw_row("Gratuity employer contribution",  "Gratuity rate 4.81%",            n(d["gratuity"]),    n(d["gratuity"]*12),   alt=alt); alt=not alt
    draw_row("Employee Health Insurance",       "Fully Taxable",                  n(d["health_ins"]),  n(d["health_ins"]*12), alt=alt); alt=not alt
    draw_row("Total Employer Contributions &\nPerquisites (B)", "",               n(d["total_ec"]),    n(d["total_ec"]*12),   is_total=True)
    draw_row("Total CTC (Fixed) (A+B) (C)",    "",                               n(d["total_ctc"]),   n(d["total_ctc"]*12),  is_grand=True)

    draw_row("PLI/Bonus/Variable Pay (Subject to\nPerformance Review & paid annually)", "Performance Pay", "-", "-", alt=False); alt=False
    draw_row("Total CTC (Including Variable) (D)", "",                            "-",                 n(d["total_ctc"]*12),  is_grand=True)

    draw_row("Employee Contribution",           "", None, None,                   is_section=True); alt=False
    draw_row("PF employee contribution",        "Employee rate 12% of 15000",     n(d["pf_emp"]),      n(d["pf_emp"]*12),     alt=alt); alt=not alt
    draw_row("ESIC employee contribution",
             "Employee rate 0.75%" if d["esic_eligible"] else "Employee rate 0.75%",
             n(d["esic_emp_amt2"]) if d["esic_eligible"] else "-",
             n(d["esic_emp_amt2"]*12) if d["esic_eligible"] else "-",            alt=alt); alt=not alt
    draw_row("Professional Tax",                "NA",                             "-",                 "-",                   alt=alt); alt=not alt
    draw_row("Total Employee Contributions (E)","",                               n(d["total_ded"]),   n(d["total_ded"]*12),  is_total=True)
    draw_row("Net take Home (Before TDS) (A-E)","",                               n(d["net_take_home"]),n(d["net_take_home"]*12), is_net=True)

    # ── Outer border around entire table ──────────────────────────────────
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(0.8)
    c.rect(M, y, TW, table_top - y, fill=0, stroke=1)

    # Vertical column dividers
    c.setLineWidth(0.4)
    c.setStrokeColorRGB(0.5, 0.5, 0.5)
    for cx in [CX[1], CX[2], CX[3]]:
        c.line(cx, y, cx, table_top)

    # ── Title: "CTC Salary Annexure-1" — bottom right, like original ─────
    y -= 10
    c.setFont(BI, 11)
    c.setFillColorRGB(0, 0, 0)
    c.drawRightString(W - M, y, "CTC Salary Annexure-1")

    # ── Notes ──────────────────────────────────────────────────────────────
    y -= 18
    c.setFont(BI, 8)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(M, y, "Note:")
    y -= 12
    c.setFont(B, 7.8)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    notes = [
        "1. ESIC & Statutory Bonus not eligible if monthly Gross Salary above Rs 21000/-",
        "2. TDS will be calculated as per the applicable provisions of the Income Tax Act, 1961, and will be deducted from your monthly",
        "   salary accordingly. The deduction will be based on the tax regime chosen by you (Old or New) and the investment declarations",
        "   made during the financial year.",
        "3. The amount mentioned for health insurance in your CTC is approximate and is subject to change. The final premium will be",
        "   determined after submission of your family members' documents and required health declarations to the insurance provider.",
    ]
    for note in notes:
        c.drawString(M, y, note)
        y -= 11

    c.save()
    buf.seek(0)
    return buf


# ════════════════════════════════════════════════════════════════════════════
# CLASSIC TEMPLATE
# ════════════════════════════════════════════════════════════════════════════
def pdf_classic(d, name, desig, dept, eid, hdr_hex, acc_hex, txt_hex, font, company):
    buf = io.BytesIO()
    c   = canvas.Canvas(buf, pagesize=A4)
    W, H = A4; M = 36
    hdr = hex_to_rgb(hdr_hex); acc = hex_to_rgb(acc_hex); txt = hex_to_rgb(txt_hex)
    B  = font
    BI = {"Helvetica": "Helvetica-Bold", "Times-Roman": "Times-Bold", "Courier": "Courier-Bold"}[font]
    CX = [M, 235, 375, 475]; CW = [199, 134, 94, 92]; TW = W - M*2

    # Header band
    c.setFillColorRGB(*hdr)
    c.rect(0, H-78, W, 78, fill=1, stroke=0)
    c.setFillColorRGB(*txt)
    c.setFont(BI, 15); c.drawString(M, H-34, "CTC Salary Annexure - 1")
    if company: c.setFont(B, 9); c.drawRightString(W-M, H-30, company)
    c.setFont(B, 8.5)
    parts = [x for x in [name, desig, dept, f"ID: {eid}" if eid else ""] if x]
    c.drawString(M, H-54, "  |  ".join(parts))
    c.drawRightString(W-M, H-54, datetime.date.today().strftime("%d %b %Y"))

    y = H - 92
    table_top = y
    # Col headers
    c.setFillColorRGB(*acc); c.rect(M, y-18, TW, 18, fill=1, stroke=0)
    c.setFillColorRGB(*txt); c.setFont(BI, 8.5)
    c.drawString(CX[0]+4, y-10, "Component")
    c.drawString(CX[1]+4, y-10, "Type")
    c.drawRightString(CX[2]+CW[2], y-10, "Monthly Amt")
    c.drawRightString(CX[3]+CW[3], y-10, "Yearly Amt")
    c.setFillColorRGB(0,0,0); y -= 18

    def row(label, typ, mo, yr, kind="data", alt=False):
        nonlocal y; rh = 15
        fills = {"section":(0.92,0.94,0.97),"total":(0.87,0.91,0.97),
                 "grand": tuple(x*0.18+0.82 for x in acc),
                 "net":   (0.82,0.94,0.84), "data": (0.97,0.97,0.99) if alt else None}
        f = fills.get(kind)
        if f: c.setFillColorRGB(*f); c.rect(M, y-rh+2, TW, rh, fill=1, stroke=0)
        bold = kind in ("section","total","grand","net")
        c.setFont(BI if bold else B, 8 if kind=="section" else 8.5)
        clr = {"grand":(0.05,0.27,0.50),"net":(0.1,0.45,0.18),"section":(0.3,0.3,0.4)}.get(kind,(0,0,0))
        c.setFillColorRGB(*clr); ty = y - rh/2 + 1
        c.drawString(CX[0]+4, ty, label)
        if kind not in ("section",):
            c.setFont(B,7.5); c.setFillColorRGB(0.45,0.45,0.45)
            if typ: c.drawString(CX[1]+4, ty, typ)
            c.setFillColorRGB(*clr); c.setFont(BI if bold else B, 8.5)
            c.drawRightString(CX[2]+CW[2], ty, mo or "-")
            c.drawRightString(CX[3]+CW[3], ty, yr or "-")
        c.setStrokeColorRGB(0.85,0.85,0.88); c.setLineWidth(0.3); c.line(M, y-rh+2, M+TW, y-rh+2)
        y -= rh

    alt=False
    row("Basic Salary","Fully Taxable",n(d["basic"]),n(d["basic"]*12),alt=alt); alt=not alt
    row("House Rent Allowance","Fully Taxable",n(d["hra"]),n(d["hra"]*12),alt=alt); alt=not alt
    row("Statutory Bonus","Fully Taxable",n(d["stat_bonus"]),n(d["stat_bonus"]*12),alt=alt); alt=not alt
    row("Conveyance/ Transport Allowance","Fully Taxable",n(d["conveyance"]),n(d["conveyance"]*12),alt=alt); alt=not alt
    row("Total Gross Salary (A)","",n(d["total_gross"]),n(d["total_gross"]*12),"total")
    row("Employer Contributions & Perquisites",None,None,None,"section"); alt=False
    row("PF employer contribution","Employer rate 12% of 15000",n(d["pf_ec"]),n(d["pf_ec"]*12),alt=alt); alt=not alt
    row("ESIC employer contribution","Employer rate 3.25%",n(d["esic_emp_amt"]) if d["esic_eligible"] else "-",n(d["esic_emp_amt"]*12) if d["esic_eligible"] else "-",alt=alt); alt=not alt
    row("Gratuity employer contribution","Gratuity rate 4.81%",n(d["gratuity"]),n(d["gratuity"]*12),alt=alt); alt=not alt
    row("Employee Health Insurance","Fully Taxable",n(d["health_ins"]),n(d["health_ins"]*12),alt=alt); alt=not alt
    row("Total Employer Contributions & Perquisites (B)","",n(d["total_ec"]),n(d["total_ec"]*12),"total")
    row("Total CTC (Fixed) (A+B) (C)","",n(d["total_ctc"]),n(d["total_ctc"]*12),"grand")
    row("PLI/Bonus/Variable Pay","Performance Pay","-","-"); alt=False
    row("Total CTC (Including Variable) (D)","","-",n(d["total_ctc"]*12),"grand")
    row("Employee Contribution",None,None,None,"section"); alt=False
    row("PF employee contribution","Employee rate 12% of 15000",n(d["pf_emp"]),n(d["pf_emp"]*12),alt=alt); alt=not alt
    row("ESIC employee contribution","Employee rate 0.75%",n(d["esic_emp_amt2"]) if d["esic_eligible"] else "-",n(d["esic_emp_amt2"]*12) if d["esic_eligible"] else "-",alt=alt); alt=not alt
    row("Professional Tax","NA","-","-",alt=alt); alt=not alt
    row("Total Employee Contributions (E)","",n(d["total_ded"]),n(d["total_ded"]*12),"total")
    row("Net take Home (Before TDS) (A-E)","",n(d["net_take_home"]),n(d["net_take_home"]*12),"net")

    c.setStrokeColorRGB(*hdr); c.setLineWidth(0.8); c.rect(M, y, TW, table_top-y, fill=0, stroke=1)
    for cx in [CX[1],CX[2],CX[3]]:
        c.setStrokeColorRGB(0.75,0.75,0.75); c.setLineWidth(0.3); c.line(cx,y,cx,table_top)

    y -= 8; c.setFont(BI,11); c.setFillColorRGB(*hdr); c.drawRightString(W-M,y,"CTC Salary Annexure-1")
    _notes(c, d, y-16, M, W, B, BI)
    c.save(); buf.seek(0); return buf


# ════════════════════════════════════════════════════════════════════════════
# MODERN TEMPLATE
# ════════════════════════════════════════════════════════════════════════════
def pdf_modern(d, name, desig, dept, eid, hdr_hex, acc_hex, txt_hex, font, company):
    buf = io.BytesIO()
    c   = canvas.Canvas(buf, pagesize=A4)
    W, H = A4; M = 36
    hdr = hex_to_rgb(hdr_hex); acc = hex_to_rgb(acc_hex); txt = hex_to_rgb(txt_hex)
    B  = font
    BI = {"Helvetica":"Helvetica-Bold","Times-Roman":"Times-Bold","Courier":"Courier-Bold"}[font]
    CX = [M,235,375,475]; CW=[199,134,94,92]; TW=W-M*2

    c.setFillColorRGB(*hdr); c.rect(0,H-88,W,88,fill=1,stroke=0)
    c.setFillColorRGB(*acc); c.rect(0,H-88,5,88,fill=1,stroke=0)
    c.setFillColorRGB(*txt); c.setFont(BI,17); c.drawString(M+8,H-36,"SALARY STRUCTURE")
    c.setFont(B,8); c.setFillColorRGB(*[min(1,x+0.4) for x in txt])
    c.drawString(M+8,H-52,"CTC Annexure — Confidential")
    if company: c.setFillColorRGB(*acc); c.setFont(BI,9); c.drawRightString(W-M,H-36,company)
    parts=[x for x in[name,desig,dept,f"ID:{eid}" if eid else ""] if x]
    c.setFillColorRGB(*[min(1,x+0.35) for x in txt]); c.setFont(B,8.5)
    c.drawString(M+8,H-68,"  ·  ".join(parts))
    c.drawRightString(W-M,H-68,datetime.date.today().strftime("%d %b %Y"))

    y=H-104; table_top=y
    c.setFillColorRGB(*acc); c.rect(M,y-18,TW,18,fill=1,stroke=0)
    c.setFillColorRGB(*txt); c.setFont(BI,8.5)
    c.drawString(CX[0]+4,y-10,"COMPONENT"); c.drawString(CX[1]+4,y-10,"TYPE")
    c.drawRightString(CX[2]+CW[2],y-10,"MONTHLY AMT"); c.drawRightString(CX[3]+CW[3],y-10,"YEARLY AMT")
    c.setFillColorRGB(0,0,0); y-=18

    def row(label,typ,mo,yr,kind="data",alt=False):
        nonlocal y; rh=15
        if kind=="section":
            c.setFillColorRGB(*[x*0.14+0.86 for x in hdr]); c.rect(M,y-rh+2,TW,rh,fill=1,stroke=0)
            c.setFillColorRGB(*[x*0.5 for x in acc]); c.setFont(BI,7.5); c.drawString(CX[0]+4,y-rh/2+1,label.upper())
            c.setStrokeColorRGB(0.87,0.87,0.9); c.setLineWidth(0.3); c.line(M,y-rh+2,M+TW,y-rh+2); y-=rh; return
        if kind=="grand":
            c.setFillColorRGB(*[x*0.15+0.85 for x in acc]); c.rect(M,y-rh+2,TW,rh,fill=1,stroke=0)
            c.setFillColorRGB(*acc); c.rect(M,y-rh+2,3,rh,fill=1,stroke=0)
            c.setFillColorRGB(*[x*0.35 for x in acc]); ty=y-rh/2+1; c.setFont(BI,9)
            c.drawString(CX[0]+7,ty,label); c.drawRightString(CX[2]+CW[2],ty,mo or "-"); c.drawRightString(CX[3]+CW[3],ty,yr or "-")
            c.setStrokeColorRGB(0.85,0.85,0.88); c.setLineWidth(0.3); c.line(M,y-rh+2,M+TW,y-rh+2); y-=rh; return
        if kind=="net":
            c.setFillColorRGB(0.06,0.48,0.32); c.rect(M,y-rh+2,TW,rh,fill=1,stroke=0)
            c.setFillColorRGB(1,1,1); ty=y-rh/2+1; c.setFont(BI,9)
            c.drawString(CX[0]+4,ty,label); c.drawRightString(CX[2]+CW[2],ty,mo or "-"); c.drawRightString(CX[3]+CW[3],ty,yr or "-")
            c.setStrokeColorRGB(0.85,0.88,0.85); c.setLineWidth(0.3); c.line(M,y-rh+2,M+TW,y-rh+2); y-=rh; return
        bold=kind=="total"
        if bold: c.setFillColorRGB(0.92,0.94,0.96); c.rect(M,y-rh+2,TW,rh,fill=1,stroke=0)
        elif alt: c.setFillColorRGB(0.97,0.97,0.99); c.rect(M,y-rh+2,TW,rh,fill=1,stroke=0)
        ty=y-rh/2+1; c.setFont(BI if bold else B,8.5); c.setFillColorRGB(0.1,0.1,0.1); c.drawString(CX[0]+4,ty,label)
        c.setFont(B,7.5); c.setFillColorRGB(0.5,0.5,0.5)
        if typ: c.drawString(CX[1]+4,ty,typ)
        c.setFillColorRGB(0.1,0.1,0.1); c.setFont(BI if bold else B,8.5)
        c.drawRightString(CX[2]+CW[2],ty,mo or "-"); c.drawRightString(CX[3]+CW[3],ty,yr or "-")
        c.setStrokeColorRGB(0.88,0.88,0.90); c.setLineWidth(0.3); c.line(M,y-rh+2,M+TW,y-rh+2); y-=rh

    alt=False
    row("Basic Salary","Fully Taxable",n(d["basic"]),n(d["basic"]*12),alt=alt); alt=not alt
    row("House Rent Allowance","Fully Taxable",n(d["hra"]),n(d["hra"]*12),alt=alt); alt=not alt
    row("Statutory Bonus","Fully Taxable",n(d["stat_bonus"]),n(d["stat_bonus"]*12),alt=alt); alt=not alt
    row("Conveyance/ Transport Allowance","Fully Taxable",n(d["conveyance"]),n(d["conveyance"]*12),alt=alt); alt=not alt
    row("Total Gross Salary (A)","",n(d["total_gross"]),n(d["total_gross"]*12),"total")
    row("Employer Contributions & Perquisites",None,None,None,"section"); alt=False
    row("PF employer contribution","Employer rate 12% of 15000",n(d["pf_ec"]),n(d["pf_ec"]*12),alt=alt); alt=not alt
    row("ESIC employer contribution","Employer rate 3.25%",n(d["esic_emp_amt"]) if d["esic_eligible"] else "-",n(d["esic_emp_amt"]*12) if d["esic_eligible"] else "-",alt=alt); alt=not alt
    row("Gratuity employer contribution","Gratuity rate 4.81%",n(d["gratuity"]),n(d["gratuity"]*12),alt=alt); alt=not alt
    row("Employee Health Insurance","Fully Taxable",n(d["health_ins"]),n(d["health_ins"]*12),alt=alt); alt=not alt
    row("Total Employer Contributions & Perquisites (B)","",n(d["total_ec"]),n(d["total_ec"]*12),"total")
    row("Total CTC (Fixed) (A+B) (C)","",n(d["total_ctc"]),n(d["total_ctc"]*12),"grand")
    row("PLI/Bonus/Variable Pay","Performance Pay","-","-"); alt=False
    row("Total CTC (Including Variable) (D)","","-",n(d["total_ctc"]*12),"grand")
    row("Employee Contribution",None,None,None,"section"); alt=False
    row("PF employee contribution","Employee rate 12% of 15000",n(d["pf_emp"]),n(d["pf_emp"]*12),alt=alt); alt=not alt
    row("ESIC employee contribution","Employee rate 0.75%",n(d["esic_emp_amt2"]) if d["esic_eligible"] else "-",n(d["esic_emp_amt2"]*12) if d["esic_eligible"] else "-",alt=alt); alt=not alt
    row("Professional Tax","NA","-","-",alt=alt)
    row("Total Employee Contributions (E)","",n(d["total_ded"]),n(d["total_ded"]*12),"total")
    row("Net take Home (Before TDS) (A-E)","",n(d["net_take_home"]),n(d["net_take_home"]*12),"net")

    c.setStrokeColorRGB(*[x*0.6 for x in hdr]); c.setLineWidth(0.8); c.rect(M,y,TW,table_top-y,fill=0,stroke=1)
    for cx in[CX[1],CX[2],CX[3]]:
        c.setStrokeColorRGB(0.78,0.78,0.80); c.setLineWidth(0.3); c.line(cx,y,cx,table_top)
    y-=8; c.setFont(BI,11); c.setFillColorRGB(*acc); c.drawRightString(W-M,y,"CTC Salary Annexure-1")
    _notes(c,d,y-16,M,W,B,BI)
    c.save(); buf.seek(0); return buf


# ════════════════════════════════════════════════════════════════════════════
# CORPORATE TEMPLATE
# ════════════════════════════════════════════════════════════════════════════
def pdf_corporate(d, name, desig, dept, eid, hdr_hex, acc_hex, txt_hex, font, company):
    buf = io.BytesIO()
    c   = canvas.Canvas(buf, pagesize=A4)
    W, H = A4; M = 36
    hdr = hex_to_rgb(hdr_hex); acc = hex_to_rgb(acc_hex); txt = hex_to_rgb(txt_hex)
    B  = font
    BI = {"Helvetica":"Helvetica-Bold","Times-Roman":"Times-Bold","Courier":"Courier-Bold"}[font]
    CX = [M,235,375,475]; CW=[199,134,94,92]; TW=W-M*2

    c.setFillColorRGB(*hdr); c.rect(0,H-86,W,86,fill=1,stroke=0)
    c.setFillColorRGB(*acc); c.rect(0,H-88,W,2,fill=1,stroke=0)
    c.setFillColorRGB(*[x*0.65 for x in hdr]); c.rect(W-110,H-86,110,86,fill=1,stroke=0)
    c.setFillColorRGB(*txt); c.setFont(BI,16); c.drawString(M,H-34,"SALARY ANNEXURE")
    c.setFont(B,8.5); c.setFillColorRGB(*[min(1,x+0.4) for x in txt]); c.drawString(M,H-50,"Confidential — CTC Breakdown")
    if company: c.setFont(BI,10); c.setFillColorRGB(*acc); c.drawRightString(W-M-8,H-34,company)
    parts=[x for x in[name,desig,dept,f"ID:{eid}" if eid else ""] if x]
    c.setFillColorRGB(*[min(1,x+0.4) for x in txt]); c.setFont(B,8.5)
    c.drawString(M,H-66,"  ·  ".join(parts))
    c.drawRightString(W-M-8,H-66,datetime.date.today().strftime("%d %b %Y"))

    y=H-102; table_top=y
    c.setFillColorRGB(*[x*0.78 for x in hdr]); c.rect(M,y-18,TW,18,fill=1,stroke=0)
    c.setFillColorRGB(*acc); c.setFont(BI,8.5)
    c.drawString(CX[0]+4,y-10,"COMPONENT"); c.drawString(CX[1]+4,y-10,"TYPE")
    c.drawRightString(CX[2]+CW[2],y-10,"MONTHLY AMT"); c.drawRightString(CX[3]+CW[3],y-10,"YEARLY AMT")
    c.setFillColorRGB(0,0,0); y-=18

    def row(label,typ,mo,yr,kind="data",alt=False):
        nonlocal y; rh=15
        if kind=="section":
            c.setFillColorRGB(*[x*0.12+0.88 for x in hdr]); c.rect(M,y-rh+2,TW,rh,fill=1,stroke=0)
            c.setFillColorRGB(*[x*0.45 for x in hdr]); c.setFont(BI,7.5); c.drawString(CX[0]+4,y-rh/2+1,label.upper())
            c.setStrokeColorRGB(0.85,0.87,0.85); c.setLineWidth(0.3); c.line(M,y-rh+2,M+TW,y-rh+2); y-=rh; return
        if kind=="grand":
            c.setFillColorRGB(*[x*0.16+0.84 for x in acc]); c.rect(M,y-rh+2,TW,rh,fill=1,stroke=0)
            c.setFillColorRGB(*acc); c.rect(M,y-rh+2,3,rh,fill=1,stroke=0)
            ty=y-rh/2+1; c.setFillColorRGB(*[x*0.38 for x in hdr]); c.setFont(BI,9)
            c.drawString(CX[0]+7,ty,label); c.drawRightString(CX[2]+CW[2],ty,mo or "-"); c.drawRightString(CX[3]+CW[3],ty,yr or "-")
            c.setStrokeColorRGB(0.85,0.88,0.85); c.setLineWidth(0.3); c.line(M,y-rh+2,M+TW,y-rh+2); y-=rh; return
        if kind=="net":
            c.setFillColorRGB(*[x*0.72 for x in hdr]); c.rect(M,y-rh+2,TW,rh,fill=1,stroke=0)
            c.setFillColorRGB(*acc); ty=y-rh/2+1; c.setFont(BI,9)
            c.drawString(CX[0]+4,ty,label); c.drawRightString(CX[2]+CW[2],ty,mo or "-"); c.drawRightString(CX[3]+CW[3],ty,yr or "-")
            c.setStrokeColorRGB(0.85,0.88,0.85); c.setLineWidth(0.3); c.line(M,y-rh+2,M+TW,y-rh+2); y-=rh; return
        bold=kind=="total"
        if bold: c.setFillColorRGB(0.90,0.93,0.91); c.rect(M,y-rh+2,TW,rh,fill=1,stroke=0)
        elif alt: c.setFillColorRGB(0.96,0.98,0.97); c.rect(M,y-rh+2,TW,rh,fill=1,stroke=0)
        ty=y-rh/2+1; c.setFont(BI if bold else B,8.5); c.setFillColorRGB(0.1,0.1,0.1); c.drawString(CX[0]+4,ty,label)
        c.setFont(B,7.5); c.setFillColorRGB(0.5,0.5,0.5)
        if typ: c.drawString(CX[1]+4,ty,typ)
        c.setFillColorRGB(0.1,0.1,0.1); c.setFont(BI if bold else B,8.5)
        c.drawRightString(CX[2]+CW[2],ty,mo or "-"); c.drawRightString(CX[3]+CW[3],ty,yr or "-")
        c.setStrokeColorRGB(0.87,0.89,0.87); c.setLineWidth(0.3); c.line(M,y-rh+2,M+TW,y-rh+2); y-=rh

    alt=False
    row("Basic Salary","Fully Taxable",n(d["basic"]),n(d["basic"]*12),alt=alt); alt=not alt
    row("House Rent Allowance","Fully Taxable",n(d["hra"]),n(d["hra"]*12),alt=alt); alt=not alt
    row("Statutory Bonus","Fully Taxable",n(d["stat_bonus"]),n(d["stat_bonus"]*12),alt=alt); alt=not alt
    row("Conveyance/ Transport Allowance","Fully Taxable",n(d["conveyance"]),n(d["conveyance"]*12),alt=alt); alt=not alt
    row("Total Gross Salary (A)","",n(d["total_gross"]),n(d["total_gross"]*12),"total")
    row("Employer Contributions & Perquisites",None,None,None,"section"); alt=False
    row("PF employer contribution","Employer rate 12% of 15000",n(d["pf_ec"]),n(d["pf_ec"]*12),alt=alt); alt=not alt
    row("ESIC employer contribution","Employer rate 3.25%",n(d["esic_emp_amt"]) if d["esic_eligible"] else "-",n(d["esic_emp_amt"]*12) if d["esic_eligible"] else "-",alt=alt); alt=not alt
    row("Gratuity employer contribution","Gratuity rate 4.81%",n(d["gratuity"]),n(d["gratuity"]*12),alt=alt); alt=not alt
    row("Employee Health Insurance","Fully Taxable",n(d["health_ins"]),n(d["health_ins"]*12),alt=alt); alt=not alt
    row("Total Employer Contributions & Perquisites (B)","",n(d["total_ec"]),n(d["total_ec"]*12),"total")
    row("Total CTC (Fixed) (A+B) (C)","",n(d["total_ctc"]),n(d["total_ctc"]*12),"grand")
    row("PLI/Bonus/Variable Pay","Performance Pay","-","-"); alt=False
    row("Total CTC (Including Variable) (D)","","-",n(d["total_ctc"]*12),"grand")
    row("Employee Contribution",None,None,None,"section"); alt=False
    row("PF employee contribution","Employee rate 12% of 15000",n(d["pf_emp"]),n(d["pf_emp"]*12),alt=alt); alt=not alt
    row("ESIC employee contribution","Employee rate 0.75%",n(d["esic_emp_amt2"]) if d["esic_eligible"] else "-",n(d["esic_emp_amt2"]*12) if d["esic_eligible"] else "-",alt=alt); alt=not alt
    row("Professional Tax","NA","-","-",alt=alt)
    row("Total Employee Contributions (E)","",n(d["total_ded"]),n(d["total_ded"]*12),"total")
    row("Net take Home (Before TDS) (A-E)","",n(d["net_take_home"]),n(d["net_take_home"]*12),"net")

    c.setStrokeColorRGB(*[x*0.5 for x in hdr]); c.setLineWidth(0.8); c.rect(M,y,TW,table_top-y,fill=0,stroke=1)
    for cx in[CX[1],CX[2],CX[3]]:
        c.setStrokeColorRGB(0.78,0.80,0.78); c.setLineWidth(0.3); c.line(cx,y,cx,table_top)
    y-=8; c.setFont(BI,11); c.setFillColorRGB(*[x*0.5 for x in hdr]); c.drawRightString(W-M,y,"CTC Salary Annexure-1")
    _notes(c,d,y-16,M,W,B,BI)
    c.save(); buf.seek(0); return buf


# ── Shared notes ──────────────────────────────────────────────────────────────
def _notes(c, d, y, M, W, B, BI):
    c.setFont(BI, 8); c.setFillColorRGB(0,0,0); c.drawString(M, y, "Note:"); y -= 12
    c.setFont(B, 7.8); c.setFillColorRGB(0.2,0.2,0.2)
    for note in [
        "1. ESIC & Statutory Bonus not eligible if monthly Gross Salary above Rs 21000/-",
        "2. TDS will be calculated as per the applicable provisions of the Income Tax Act, 1961, and will be deducted from your monthly",
        "   salary accordingly. The deduction will be based on the tax regime chosen by you (Old or New) and the investment declarations",
        "   made during the financial year.",
        "3. The amount mentioned for health insurance in your CTC is approximate and is subject to change. The final premium will be",
        "   determined after submission of your family members' documents and required health declarations to the insurance provider.",
    ]:
        c.drawString(M, y, note); y -= 11


PDF_BUILDERS = {
    "original":  pdf_original,
    "classic":   pdf_classic,
    "modern":    pdf_modern,
    "corporate": pdf_corporate,
}


# ── Trigger ───────────────────────────────────────────────────────────────────
if calc_btn and net_input:
    st.session_state.update({
        "d": calc_ctc(int(net_input)),
        "name": emp_name, "desig": emp_desig,
        "dept": emp_dept, "eid": emp_id,
        "hdr": custom_header, "acc": custom_accent,
        "txt": custom_text,   "font": font_choice,
        "company": company_name,
    })

# ── Display ───────────────────────────────────────────────────────────────────
if "d" in st.session_state:
    d      = st.session_state["d"]
    name   = st.session_state["name"]
    desig  = st.session_state["desig"]
    dept   = st.session_state.get("dept","")
    eid    = st.session_state.get("eid","")
    hdr    = st.session_state.get("hdr", custom_header)
    acc    = st.session_state.get("acc", custom_accent)
    txt_c  = st.session_state.get("txt", custom_text)
    font   = st.session_state.get("font", font_choice)
    company= st.session_state.get("company", company_name)
    tmpl   = st.session_state["template"]

    st.divider()
    if name:
        st.subheader(f"📄 {name}" + (f" — {desig}" if desig else ""))

    m1, m2, m3 = st.columns(3)
    m1.metric("Monthly CTC",   fmt(d["total_ctc"]))
    m2.metric("Annual CTC",    fmt(d["total_ctc"]*12))
    m3.metric("Net Take-Home", fmt(d["net_take_home"]))

    st.divider()
    cw = [4, 2.5, 1.8, 1.8]
    h = st.columns(cw)
    h[0].markdown("**Component**"); h[1].markdown("**Type**")
    h[2].markdown("**Monthly**");   h[3].markdown("**Yearly**")
    st.markdown("---")
    table_row(cw,"Basic Salary","Fully Taxable",d["basic"],d["basic"]*12)
    table_row(cw,"House Rent Allowance","Fully Taxable",d["hra"],d["hra"]*12)
    table_row(cw,"Statutory Bonus","Fully Taxable",d["stat_bonus"],d["stat_bonus"]*12)
    table_row(cw,"Conveyance/ Transport Allowance","Fully Taxable",d["conveyance"],d["conveyance"]*12)
    st.markdown(f"<div class='grand-total'>Total Gross Salary (A) &nbsp;|&nbsp; {fmt(d['total_gross'])} / mo &nbsp;|&nbsp; {fmt(d['total_gross']*12)} / yr</div>",unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Employer Contributions & Perquisites</div>",unsafe_allow_html=True)
    table_row(cw,"PF employer contribution","Employer rate 12% of 15000",d["pf_ec"],d["pf_ec"]*12)
    table_row(cw,"ESIC employer contribution","Employer rate 3.25%" if d["esic_eligible"] else "Not Eligible",d["esic_emp_amt"] if d["esic_eligible"] else None,d["esic_emp_amt"]*12 if d["esic_eligible"] else None)
    table_row(cw,"Gratuity employer contribution","Gratuity rate 4.81%",d["gratuity"],d["gratuity"]*12)
    table_row(cw,"Employee Health Insurance","Fully Taxable",d["health_ins"],d["health_ins"]*12)
    st.markdown(f"<div class='grand-total'>Total Employer Contributions & Perquisites (B) &nbsp;|&nbsp; {fmt(d['total_ec'])} / mo &nbsp;|&nbsp; {fmt(d['total_ec']*12)} / yr</div>",unsafe_allow_html=True)
    st.markdown(f"<div class='grand-total'>Total CTC Fixed (A+B) (C) &nbsp;|&nbsp; {fmt(d['total_ctc'])} / mo &nbsp;|&nbsp; {fmt(d['total_ctc']*12)} / yr</div>",unsafe_allow_html=True)
    st.markdown("<div class='section-title'>PLI / Bonus / Variable Pay</div>",unsafe_allow_html=True)
    table_row(cw,"Performance Pay","Subject to Performance Review",None,None)
    st.markdown(f"<div class='grand-total'>Total CTC Including Variable (D) &nbsp;|&nbsp; Annual: {fmt(d['total_ctc']*12)}</div>",unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Employee Contributions</div>",unsafe_allow_html=True)
    table_row(cw,"PF employee contribution","Employee rate 12% of 15000",d["pf_emp"],d["pf_emp"]*12)
    table_row(cw,"ESIC employee contribution","Employee rate 0.75%" if d["esic_eligible"] else "Not Eligible",d["esic_emp_amt2"] if d["esic_eligible"] else None,d["esic_emp_amt2"]*12 if d["esic_eligible"] else None)
    table_row(cw,"Professional Tax","NA",None,None)
    table_row(cw,"Total Employee Contributions (E)","",d["total_ded"],d["total_ded"]*12,bold=True)
    st.markdown(f"<div class='net-total'>Net Take Home Before TDS (A−E) &nbsp;|&nbsp; {fmt(d['net_take_home'])} / mo &nbsp;|&nbsp; {fmt(d['net_take_home']*12)} / yr</div>",unsafe_allow_html=True)

    st.divider()
    esic_note = f"ESIC {'applicable' if d['esic_eligible'] else 'not applicable'} — gross ₹{d['gross']:,.0f} is {'below' if d['esic_eligible'] else 'above'} ₹21,000."
    st.info(f"**Notes:** {esic_note} | TDS per Income Tax Act 1961. | Health insurance approximate.")

    pdf_buf = PDF_BUILDERS[tmpl](d, name, desig, dept, eid, hdr, acc, txt_c, font, company)
    fname   = f"CTC_{(name or 'Employee').replace(' ','_')}_{tmpl}.pdf"
    st.markdown(f"**Downloading:** `{TEMPLATES[tmpl]['name']}` template")
    st.download_button(
        label=f"⬇️ Download PDF — {TEMPLATES[tmpl]['name']} Template",
        data=pdf_buf, file_name=fname,
        mime="application/pdf",
        use_container_width=True, type="primary"
    )
