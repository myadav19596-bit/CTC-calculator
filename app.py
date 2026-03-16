import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
import io

st.set_page_config(page_title="CTC Structure Generator", page_icon="💼", layout="centered")

st.markdown("""
<style>
    .block-container { max-width: 780px; padding-top: 2rem; }
    .section-title { background:#eef2f7; padding:6px 12px; border-radius:6px; font-weight:600; font-size:0.83rem; color:#555; margin:10px 0 4px 0; }
    .grand-total  { background:#dce8f7; padding:8px 14px; border-radius:6px; font-weight:600; color:#1a5fa8; margin:4px 0; }
    .net-total    { background:#d4edda; padding:8px 14px; border-radius:6px; font-weight:600; color:#2d7a3a; margin:4px 0; }
    .tmpl-card { border:1.5px solid var(--color-border-tertiary); border-radius:10px; padding:14px; cursor:pointer; transition:border-color 0.15s; }
    .tmpl-card.selected { border-color:#185FA5; background:#f0f6ff; }
    .tmpl-preview { width:100%; height:90px; border-radius:6px; margin-bottom:8px; display:flex; align-items:center; justify-content:center; font-size:11px; font-weight:600; letter-spacing:0.05em; }
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
    emp_dept = st.text_input("Department",      placeholder="e.g. Engineering")
with c4:
    emp_id   = st.text_input("Employee ID",     placeholder="e.g. EMP-001")

net_input = st.number_input(
    "Net Take-Home Salary (Monthly ₹)",
    min_value=1000, max_value=10000000, value=None,
    step=500, placeholder="e.g. 69000", format="%d"
)

# ── Template Picker ───────────────────────────────────────────────────────────
st.markdown("#### 🎨 Choose PDF Template")

TEMPLATES = {
    "classic":    {"name": "Classic",    "desc": "Clean blue header, standard layout",         "bg": "#1a5fa8", "fg": "#ffffff", "accent": "#1a5fa8"},
    "modern":     {"name": "Modern",     "desc": "Dark slate header, coloured accent rows",     "bg": "#1e2a3a", "fg": "#ffffff", "accent": "#00b4a6"},
    "minimal":    {"name": "Minimal",    "desc": "All white, thin lines, typography-first",     "bg": "#ffffff", "fg": "#111111", "accent": "#444444"},
    "corporate":  {"name": "Corporate",  "desc": "Deep green professional style",               "bg": "#1a4731", "fg": "#ffffff", "accent": "#2d7a4f"},
}

if "template" not in st.session_state:
    st.session_state["template"] = "classic"

cols = st.columns(4)
for i, (key, tmpl) in enumerate(TEMPLATES.items()):
    with cols[i]:
        selected = st.session_state["template"] == key
        border   = "2px solid #185FA5" if selected else "1px solid #ddd"
        bg_card  = "#f0f6ff" if selected else "transparent"
        st.markdown(f"""
        <div style="border:{border};border-radius:10px;padding:12px;background:{bg_card};cursor:pointer">
          <div style="background:{tmpl['bg']};border-radius:6px;height:60px;margin-bottom:8px;
               display:flex;align-items:center;justify-content:center">
            <span style="color:{tmpl['fg']};font-size:10px;font-weight:600;letter-spacing:0.05em">
              {tmpl['name'].upper()}
            </span>
          </div>
          <div style="font-size:12px;font-weight:600;color:{'#185FA5' if selected else '#333'}">{tmpl['name']}</div>
          <div style="font-size:11px;color:#888;margin-top:2px;line-height:1.4">{tmpl['desc']}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Select" if not selected else "✓ Selected", key=f"tmpl_{key}",
                     use_container_width=True,
                     type="primary" if selected else "secondary"):
            st.session_state["template"] = key
            st.rerun()

# ── Colour customisation (shown for all templates) ───────────────────────────
with st.expander("🖌️ Customise colours & font"):
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        custom_header = st.color_picker("Header colour",  TEMPLATES[st.session_state["template"]]["bg"])
    with cc2:
        custom_accent = st.color_picker("Accent colour",  TEMPLATES[st.session_state["template"]]["accent"])
    with cc3:
        custom_text   = st.color_picker("Header text",    TEMPLATES[st.session_state["template"]]["fg"])
    font_choice = st.selectbox("Font style", ["Helvetica", "Times-Roman", "Courier"], index=0)
    show_logo_text = st.text_input("Company name on PDF (optional)", placeholder="e.g. Acme Pvt. Ltd.")

calc_btn = st.button("🔢 Calculate CTC Structure", type="primary", use_container_width=True)


# ── Calculation ───────────────────────────────────────────────────────────────
def calc_ctc(net_monthly):
    pf_emp = 1800
    gross  = net_monthly + pf_emp
    esic_eligible  = gross < 21000
    esic_emp_amt   = round(gross * 0.0325) if esic_eligible else 0
    esic_emp_amt2  = round(gross * 0.0075) if esic_eligible else 0
    ctc        = (gross + 2300 + esic_emp_amt) / (1 - 0.02405)
    basic      = round(ctc * 0.50)
    hra        = round(basic * 0.50)
    stat_bonus = round(basic * 0.15)
    conveyance = gross - basic - hra - stat_bonus
    gratuity   = round(basic * 0.0481)
    health_ins = 500
    pf_ec      = 1800
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


# ── PDF helpers ───────────────────────────────────────────────────────────────
def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16)/255 for i in (0, 2, 4))

def hex_to_rl(h):
    r,g,b = hex_to_rgb(h)
    return colors.Color(r, g, b)

def darken(h, factor=0.75):
    r,g,b = hex_to_rgb(h)
    return colors.Color(r*factor, g*factor, b*factor)

def lighten(h, factor=0.92):
    r,g,b = hex_to_rgb(h)
    return colors.Color(min(1,r+(1-r)*(1-factor)), min(1,g+(1-g)*(1-factor)), min(1,b+(1-b)*(1-factor)))


# ── Build rows data ───────────────────────────────────────────────────────────
def build_rows(d):
    def r(label, typ, mo, yr):
        return [label, typ,
                f"{mo:,.2f}" if mo is not None else "-",
                f"{yr:,.2f}" if yr is not None else "-"]
    rows = [
        ("section", "Fixed Allowances", None, None, None),
        ("data",  *r("Basic Salary",                    "Fully Taxable",            d["basic"],      d["basic"]*12)),
        ("data",  *r("House Rent Allowance",             "Fully Taxable",            d["hra"],        d["hra"]*12)),
        ("data",  *r("Statutory Bonus",                  "Fully Taxable",            d["stat_bonus"], d["stat_bonus"]*12)),
        ("data",  *r("Conveyance / Transport Allowance", "Fully Taxable",            d["conveyance"], d["conveyance"]*12)),
        ("total", *r("Total Gross Salary (A)",           "",                         d["total_gross"],d["total_gross"]*12)),
        ("section","Employer Contributions & Perquisites", None, None, None),
        ("data",  *r("PF employer contribution",         "Employer rate 12% of 15000", d["pf_ec"],    d["pf_ec"]*12)),
        ("data",  *r("ESIC employer contribution",
                     "Employer rate 3.25%" if d["esic_eligible"] else "Not Eligible",
                     d["esic_emp_amt"] if d["esic_eligible"] else None,
                     d["esic_emp_amt"]*12 if d["esic_eligible"] else None)),
        ("data",  *r("Gratuity employer contribution",   "Gratuity rate 4.81%",      d["gratuity"],   d["gratuity"]*12)),
        ("data",  *r("Employee Health Insurance",        "Fully Taxable",            d["health_ins"], d["health_ins"]*12)),
        ("total", *r("Total Employer Contributions & Perquisites (B)", "",           d["total_ec"],   d["total_ec"]*12)),
        ("grand", *r("Total CTC (Fixed) (A+B) (C)",     "",                         d["total_ctc"],  d["total_ctc"]*12)),
        ("section","PLI / Bonus / Variable Pay", None, None, None),
        ("data",  *r("Performance Pay",                  "Subject to Performance Review & paid annually", None, None)),
        ("grand", *r("Total CTC (Including Variable) (D)", "",                      d["total_ctc"],  d["total_ctc"]*12)),
        ("section","Employee Contributions", None, None, None),
        ("data",  *r("PF employee contribution",         "Employee rate 12% of 15000", d["pf_emp"],   d["pf_emp"]*12)),
        ("data",  *r("ESIC employee contribution",
                     "Employee rate 0.75%" if d["esic_eligible"] else "Not Eligible",
                     d["esic_emp_amt2"] if d["esic_eligible"] else None,
                     d["esic_emp_amt2"]*12 if d["esic_eligible"] else None)),
        ("data",  *r("Professional Tax",                 "NA",                       None, None)),
        ("total", *r("Total Employee Contributions (E)", "",                         d["total_ded"],  d["total_ded"]*12)),
        ("net",   *r("Net Take Home (Before TDS) (A-E)", "",                        d["net_take_home"], d["net_take_home"]*12)),
    ]
    return rows


# ════════════════════════════════════════════════════════════════════════════
# TEMPLATE 1 — CLASSIC  (blue header, light alternating rows)
# ════════════════════════════════════════════════════════════════════════════
def pdf_classic(d, name, desig, dept, eid, hdr_hex, acc_hex, txt_hex, font, company):
    buf = io.BytesIO()
    c   = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    M    = 36
    hdr  = hex_to_rgb(hdr_hex)
    acc  = hex_to_rgb(acc_hex)
    txt  = hex_to_rgb(txt_hex)
    B    = font
    BI   = font + "-Bold" if font == "Courier" else font + "-Bold" if font=="Times-Roman" else "Helvetica-Bold"
    if font == "Times-Roman": BI = "Times-Bold"
    if font == "Courier":     BI = "Courier-Bold"

    # Header band
    c.setFillColorRGB(*hdr)
    c.rect(0, H-80, W, 80, fill=1, stroke=0)
    c.setFillColorRGB(*txt)
    c.setFont(BI, 16)
    c.drawString(M, H-38, "CTC Salary Annexure - 1")
    c.setFont(B, 9)
    if company:
        c.drawRightString(W-M, H-28, company)
    c.setFont(B, 9)
    info_parts = [x for x in [name, desig, dept, f"ID: {eid}" if eid else ""] if x]
    c.drawString(M, H-58, "  |  ".join(info_parts))
    c.setFont(B, 8)
    import datetime
    c.drawRightString(W-M, H-58, f"Generated: {datetime.date.today().strftime('%d %b %Y')}")

    y = H - 100

    # Column header
    c.setFillColorRGB(*acc)
    c.rect(M, y-4, W-M*2, 18, fill=1, stroke=0)
    c.setFillColorRGB(*txt)
    c.setFont(BI, 8.5)
    CX = [M, 240, 370, 470]
    CW = [194, 124, 94, 90]
    c.drawString(CX[0]+4, y+8, "Component")
    c.drawString(CX[1]+4, y+8, "Type")
    c.drawRightString(CX[2]+CW[2], y+8, "Monthly (₹)")
    c.drawRightString(CX[3]+CW[3], y+8, "Yearly (₹)")
    c.setFillColorRGB(0,0,0)
    y -= 20

    alt = False
    rows = build_rows(d)
    for row in rows:
        kind = row[0]; label = row[1]; typ = row[2]; mo = row[3]; yr = row[4]
        rh = 15

        if kind == "section":
            c.setFillColorRGB(0.92, 0.94, 0.97)
            c.rect(M, y-4, W-M*2, rh, fill=1, stroke=0)
            c.setFillColorRGB(*[x*0.6 for x in acc])
            c.setFont(BI, 8)
            c.drawString(CX[0]+4, y+7, label)
            c.setFillColorRGB(0,0,0); y -= rh; alt = False; continue

        if kind in ("grand",):
            r2,g2,b2 = hex_to_rgb(acc_hex)
            c.setFillColorRGB(r2*0.18+0.82, g2*0.18+0.82, b2*0.18+0.82)
            c.rect(M, y-4, W-M*2, rh+2, fill=1, stroke=0)
            c.setFillColorRGB(*[x*0.55 for x in acc])
            c.setFont(BI, 9)
            c.drawString(CX[0]+4, y+8, label)
            c.drawRightString(CX[2]+CW[2], y+8, mo)
            c.drawRightString(CX[3]+CW[3], y+8, yr)
            c.setFillColorRGB(0,0,0); y -= rh+4; continue

        if kind == "net":
            c.setFillColorRGB(0.82, 0.94, 0.84)
            c.rect(M, y-4, W-M*2, rh+2, fill=1, stroke=0)
            c.setFillColorRGB(0.1,0.45,0.18)
            c.setFont(BI, 9)
            c.drawString(CX[0]+4, y+8, label)
            c.drawRightString(CX[2]+CW[2], y+8, mo)
            c.drawRightString(CX[3]+CW[3], y+8, yr)
            c.setFillColorRGB(0,0,0); y -= rh+4; continue

        if kind == "total":
            c.setFillColorRGB(0.87, 0.91, 0.97)
            c.rect(M, y-4, W-M*2, rh, fill=1, stroke=0)
            c.setFont(BI, 8.5)
        else:
            if alt:
                c.setFillColorRGB(0.97, 0.97, 0.99)
                c.rect(M, y-4, W-M*2, rh, fill=1, stroke=0)
            c.setFont(B, 8.5)
            alt = not alt

        c.setFillColorRGB(0.15,0.15,0.15)
        c.drawString(CX[0]+4, y+7, label)
        c.setFont(B, 7.5); c.setFillColorRGB(0.45,0.45,0.45)
        if typ: c.drawString(CX[1]+4, y+7, typ)
        c.setFillColorRGB(0.15,0.15,0.15)
        c.setFont(BI if kind=="total" else B, 8.5)
        c.drawRightString(CX[2]+CW[2], y+7, mo)
        c.drawRightString(CX[3]+CW[3], y+7, yr)
        c.setStrokeColorRGB(0.88,0.88,0.9); c.line(M, y-4, W-M, y-4)
        y -= rh

    _add_notes(c, d, y-10, M, W, B, BI)
    c.save(); buf.seek(0); return buf


# ════════════════════════════════════════════════════════════════════════════
# TEMPLATE 2 — MODERN  (dark header, teal accent, bold numbers)
# ════════════════════════════════════════════════════════════════════════════
def pdf_modern(d, name, desig, dept, eid, hdr_hex, acc_hex, txt_hex, font, company):
    buf = io.BytesIO()
    c   = canvas.Canvas(buf, pagesize=A4)
    W, H = A4; M = 36
    hdr = hex_to_rgb(hdr_hex); acc = hex_to_rgb(acc_hex); txt = hex_to_rgb(txt_hex)
    B = font
    BI = "Helvetica-Bold" if font=="Helvetica" else ("Times-Bold" if font=="Times-Roman" else "Courier-Bold")

    # Full-width dark header
    c.setFillColorRGB(*hdr)
    c.rect(0, H-90, W, 90, fill=1, stroke=0)
    # Left accent bar
    c.setFillColorRGB(*acc)
    c.rect(0, H-90, 6, 90, fill=1, stroke=0)

    c.setFillColorRGB(*txt)
    c.setFont(BI, 18)
    c.drawString(M+6, H-36, "SALARY STRUCTURE")
    c.setFont(B, 9)
    c.setFillColorRGB(*[min(1,x+0.4) for x in txt])
    c.drawString(M+6, H-54, "CTC Annexure — Confidential")
    if company:
        c.setFillColorRGB(*acc)
        c.drawRightString(W-M, H-36, company)
    c.setFillColorRGB(*[min(1,x+0.4) for x in txt])
    c.setFont(B, 8.5)
    info_parts = [x for x in [name, desig, dept, f"EMP ID: {eid}" if eid else ""] if x]
    c.drawString(M+6, H-70, "  ·  ".join(info_parts))
    import datetime
    c.drawRightString(W-M, H-70, datetime.date.today().strftime("%d %b %Y"))

    y = H - 110
    CX = [M, 240, 365, 468]
    CW = [194, 119, 97, 90]

    # Column headers
    c.setFillColorRGB(*acc)
    c.rect(M, y-4, W-M*2, 20, fill=1, stroke=0)
    c.setFillColorRGB(*txt)
    c.setFont(BI, 8.5)
    c.drawString(CX[0]+5, y+9, "COMPONENT")
    c.drawString(CX[1]+5, y+9, "TYPE")
    c.drawRightString(CX[2]+CW[2], y+9, "MONTHLY (₹)")
    c.drawRightString(CX[3]+CW[3], y+9, "YEARLY (₹)")
    c.setFillColorRGB(0,0,0); y -= 22

    rows = build_rows(d)
    for row in rows:
        kind=row[0]; label=row[1]; typ=row[2]; mo=row[3]; yr=row[4]; rh=15

        if kind == "section":
            c.setFillColorRGB(*[x*0.12+0.88 for x in hex_to_rgb(hdr_hex)])
            c.rect(M, y-4, W-M*2, rh, fill=1, stroke=0)
            c.setFillColorRGB(*[x*0.6 for x in acc])
            c.setFont(BI, 7.5)
            c.drawString(CX[0]+5, y+7, label.upper())
            c.setFillColorRGB(0,0,0); y -= rh; continue

        if kind == "grand":
            c.setFillColorRGB(*[x*0.15+0.85 for x in acc])
            c.rect(M, y-4, W-M*2, rh+2, fill=1, stroke=0)
            # left accent tick
            c.setFillColorRGB(*acc)
            c.rect(M, y-4, 3, rh+2, fill=1, stroke=0)
            c.setFillColorRGB(*[x*0.35 for x in acc])
            c.setFont(BI, 9)
            c.drawString(CX[0]+8, y+8, label)
            c.drawRightString(CX[2]+CW[2], y+8, mo)
            c.drawRightString(CX[3]+CW[3], y+8, yr)
            c.setFillColorRGB(0,0,0); y -= rh+4; continue

        if kind == "net":
            c.setFillColorRGB(0.06, 0.55, 0.38)
            c.rect(M, y-4, W-M*2, rh+2, fill=1, stroke=0)
            c.setFillColorRGB(1,1,1)
            c.setFont(BI, 9)
            c.drawString(CX[0]+8, y+8, label)
            c.drawRightString(CX[2]+CW[2], y+8, mo)
            c.drawRightString(CX[3]+CW[3], y+8, yr)
            c.setFillColorRGB(0,0,0); y -= rh+4; continue

        if kind == "total":
            c.setFillColorRGB(0.94,0.94,0.96)
            c.rect(M, y-4, W-M*2, rh, fill=1, stroke=0)
            c.setFont(BI, 8.5)
        else:
            c.setFont(B, 8.5)

        c.setFillColorRGB(0.1,0.1,0.1)
        c.drawString(CX[0]+5, y+7, label)
        c.setFont(B, 7.5); c.setFillColorRGB(0.5,0.5,0.5)
        if typ: c.drawString(CX[1]+5, y+7, typ)
        c.setFillColorRGB(0.1,0.1,0.1)
        c.setFont(BI if kind=="total" else B, 8.5)
        c.drawRightString(CX[2]+CW[2], y+7, mo)
        c.drawRightString(CX[3]+CW[3], y+7, yr)
        c.setStrokeColorRGB(0.9,0.9,0.92); c.line(M, y-4, W-M, y-4)
        y -= rh

    _add_notes(c, d, y-10, M, W, B, BI)
    c.save(); buf.seek(0); return buf


# ════════════════════════════════════════════════════════════════════════════
# TEMPLATE 3 — MINIMAL  (white, thin lines, elegant typography)
# ════════════════════════════════════════════════════════════════════════════
def pdf_minimal(d, name, desig, dept, eid, hdr_hex, acc_hex, txt_hex, font, company):
    buf = io.BytesIO()
    c   = canvas.Canvas(buf, pagesize=A4)
    W, H = A4; M = 50
    acc = hex_to_rgb(acc_hex)
    B = font
    BI = "Helvetica-Bold" if font=="Helvetica" else ("Times-Bold" if font=="Times-Roman" else "Courier-Bold")

    # Thin top rule
    c.setFillColorRGB(*acc)
    c.rect(M, H-42, W-M*2, 1.5, fill=1, stroke=0)

    c.setFillColorRGB(*acc)
    c.setFont(BI, 20)
    c.drawString(M, H-68, "CTC STRUCTURE")
    c.setFillColorRGB(0.5,0.5,0.5)
    c.setFont(B, 9)
    if company: c.drawRightString(W-M, H-68, company)
    c.setFillColorRGB(0.35,0.35,0.35)
    c.setFont(B, 9)
    info_parts = [x for x in [name, desig, dept, eid] if x]
    c.drawString(M, H-84, "  /  ".join(info_parts))
    import datetime
    c.drawRightString(W-M, H-84, datetime.date.today().strftime("%d %b %Y"))

    # Thin rule
    c.setStrokeColorRGB(0.85,0.85,0.85)
    c.line(M, H-92, W-M, H-92)

    y = H - 112
    CX = [M, 238, 362, 462]
    CW = [183, 118, 94, 90]

    # Column headers — minimal, just text
    c.setFillColorRGB(0.5,0.5,0.5)
    c.setFont(B, 7.5)
    c.drawString(CX[0], y+4, "COMPONENT")
    c.drawString(CX[1], y+4, "TYPE")
    c.drawRightString(CX[2]+CW[2], y+4, "MONTHLY (₹)")
    c.drawRightString(CX[3]+CW[3], y+4, "YEARLY (₹)")
    c.setStrokeColorRGB(0.7,0.7,0.7); c.line(M, y-2, W-M, y-2)
    c.setFillColorRGB(0,0,0); y -= 16

    rows = build_rows(d)
    for row in rows:
        kind=row[0]; label=row[1]; typ=row[2]; mo=row[3]; yr=row[4]; rh=15

        if kind == "section":
            y -= 4
            c.setFillColorRGB(*acc)
            c.setFont(BI, 7.5)
            c.drawString(CX[0], y+7, label.upper())
            c.setStrokeColorRGB(0.88,0.88,0.88); c.line(M, y-2, W-M, y-2)
            c.setFillColorRGB(0,0,0); y -= 14; continue

        if kind == "grand":
            y -= 2
            c.setStrokeColorRGB(*acc); c.line(M, y+rh+2, W-M, y+rh+2)
            c.setFillColorRGB(*acc)
            c.setFont(BI, 9.5)
            c.drawString(CX[0], y+8, label)
            c.drawRightString(CX[2]+CW[2], y+8, mo)
            c.drawRightString(CX[3]+CW[3], y+8, yr)
            c.setStrokeColorRGB(*acc); c.line(M, y-3, W-M, y-3)
            c.setFillColorRGB(0,0,0); y -= rh+4; continue

        if kind == "net":
            y -= 2
            c.setFillColorRGB(0.1,0.55,0.25)
            c.setFont(BI, 9.5)
            c.drawString(CX[0], y+8, label)
            c.drawRightString(CX[2]+CW[2], y+8, mo)
            c.drawRightString(CX[3]+CW[3], y+8, yr)
            c.setStrokeColorRGB(0.1,0.55,0.25); c.line(M, y-3, W-M, y-3)
            c.setFillColorRGB(0,0,0); y -= rh+4; continue

        if kind == "total":
            c.setFillColorRGB(0.15,0.15,0.15)
            c.setFont(BI, 8.5)
        else:
            c.setFillColorRGB(0.2,0.2,0.2)
            c.setFont(B, 8.5)

        c.drawString(CX[0], y+7, label)
        c.setFont(B, 7.5); c.setFillColorRGB(0.55,0.55,0.55)
        if typ: c.drawString(CX[1], y+7, typ)
        c.setFillColorRGB(0.15,0.15,0.15)
        c.setFont(BI if kind=="total" else B, 8.5)
        c.drawRightString(CX[2]+CW[2], y+7, mo)
        c.drawRightString(CX[3]+CW[3], y+7, yr)
        c.setStrokeColorRGB(0.92,0.92,0.92); c.line(M, y-3, W-M, y-3)
        y -= rh

    _add_notes(c, d, y-10, M, W, B, BI)
    c.save(); buf.seek(0); return buf


# ════════════════════════════════════════════════════════════════════════════
# TEMPLATE 4 — CORPORATE  (deep green, white on dark header, gold accent)
# ════════════════════════════════════════════════════════════════════════════
def pdf_corporate(d, name, desig, dept, eid, hdr_hex, acc_hex, txt_hex, font, company):
    buf = io.BytesIO()
    c   = canvas.Canvas(buf, pagesize=A4)
    W, H = A4; M = 36
    hdr = hex_to_rgb(hdr_hex); acc = hex_to_rgb(acc_hex); txt = hex_to_rgb(txt_hex)
    B = font
    BI = "Helvetica-Bold" if font=="Helvetica" else ("Times-Bold" if font=="Times-Roman" else "Courier-Bold")

    # Header + diagonal accent strip
    c.setFillColorRGB(*hdr)
    c.rect(0, H-88, W, 88, fill=1, stroke=0)
    # gold rule under header
    c.setFillColorRGB(*acc)
    c.rect(0, H-90, W, 2, fill=1, stroke=0)
    # Right decorative block
    c.setFillColorRGB(*[x*0.7 for x in hdr])
    c.rect(W-120, H-88, 120, 88, fill=1, stroke=0)

    c.setFillColorRGB(*txt)
    c.setFont(BI, 17)
    c.drawString(M, H-34, "SALARY ANNEXURE")
    c.setFont(B, 8.5)
    c.setFillColorRGB(*[min(1,x+0.45) for x in txt])
    c.drawString(M, H-52, "Confidential — CTC Breakdown")
    if company:
        c.setFont(BI, 10)
        c.setFillColorRGB(*acc)
        c.drawRightString(W-M-10, H-34, company)
    c.setFont(B, 8.5)
    c.setFillColorRGB(*[min(1,x+0.45) for x in txt])
    info_parts = [x for x in [name, desig, dept, f"ID: {eid}" if eid else ""] if x]
    c.drawString(M, H-68, "  ·  ".join(info_parts))
    import datetime
    c.drawRightString(W-M-10, H-68, datetime.date.today().strftime("%d %b %Y"))

    y = H - 108
    CX = [M, 240, 365, 466]
    CW = [194, 119, 95, 90]

    # Column header
    c.setFillColorRGB(*[x*0.82 for x in hdr])
    c.rect(M, y-4, W-M*2, 20, fill=1, stroke=0)
    c.setFillColorRGB(*acc)
    c.setFont(BI, 8.5)
    c.drawString(CX[0]+5, y+9, "COMPONENT")
    c.drawString(CX[1]+5, y+9, "TYPE")
    c.drawRightString(CX[2]+CW[2], y+9, "MONTHLY (₹)")
    c.drawRightString(CX[3]+CW[3], y+9, "YEARLY (₹)")
    c.setFillColorRGB(0,0,0); y -= 22

    rows = build_rows(d)
    alt = False
    for row in rows:
        kind=row[0]; label=row[1]; typ=row[2]; mo=row[3]; yr=row[4]; rh=15

        if kind == "section":
            c.setFillColorRGB(*[x*0.15+0.85 for x in hdr])
            c.rect(M, y-4, W-M*2, rh, fill=1, stroke=0)
            c.setFillColorRGB(*[x*0.5 for x in hdr])
            c.setFont(BI, 8)
            c.drawString(CX[0]+5, y+7, label.upper())
            c.setFillColorRGB(0,0,0); y -= rh; alt=False; continue

        if kind == "grand":
            c.setFillColorRGB(*[x*0.18+0.82 for x in acc])
            c.rect(M, y-4, W-M*2, rh+2, fill=1, stroke=0)
            c.setFillColorRGB(*acc)
            c.rect(M, y-4, 3, rh+2, fill=1, stroke=0)
            c.setFillColorRGB(*[x*0.4 for x in hdr])
            c.setFont(BI, 9)
            c.drawString(CX[0]+8, y+8, label)
            c.drawRightString(CX[2]+CW[2], y+8, mo)
            c.drawRightString(CX[3]+CW[3], y+8, yr)
            c.setFillColorRGB(0,0,0); y -= rh+4; continue

        if kind == "net":
            c.setFillColorRGB(*[x*0.8 for x in hdr])
            c.rect(M, y-4, W-M*2, rh+2, fill=1, stroke=0)
            c.setFillColorRGB(*acc)
            c.setFont(BI, 9)
            c.drawString(CX[0]+8, y+8, label)
            c.drawRightString(CX[2]+CW[2], y+8, mo)
            c.drawRightString(CX[3]+CW[3], y+8, yr)
            c.setFillColorRGB(0,0,0); y -= rh+4; continue

        if kind == "total":
            c.setFillColorRGB(0.92,0.94,0.93)
            c.rect(M, y-4, W-M*2, rh, fill=1, stroke=0)
            c.setFont(BI, 8.5)
        else:
            if alt:
                c.setFillColorRGB(0.97,0.98,0.97)
                c.rect(M, y-4, W-M*2, rh, fill=1, stroke=0)
            c.setFont(B, 8.5)
            alt = not alt

        c.setFillColorRGB(0.12,0.12,0.12)
        c.drawString(CX[0]+5, y+7, label)
        c.setFont(B, 7.5); c.setFillColorRGB(0.48,0.48,0.48)
        if typ: c.drawString(CX[1]+5, y+7, typ)
        c.setFillColorRGB(0.12,0.12,0.12)
        c.setFont(BI if kind=="total" else B, 8.5)
        c.drawRightString(CX[2]+CW[2], y+7, mo)
        c.drawRightString(CX[3]+CW[3], y+7, yr)
        c.setStrokeColorRGB(0.88,0.9,0.88); c.line(M, y-4, W-M, y-4)
        y -= rh

    _add_notes(c, d, y-10, M, W, B, BI)
    c.save(); buf.seek(0); return buf


# ── Shared notes footer ───────────────────────────────────────────────────────
def _add_notes(c, d, y, M, W, B, BI):
    y -= 4
    c.setFont(BI, 7.5); c.setFillColorRGB(0.2,0.2,0.2)
    c.drawString(M, y, "Note:"); y -= 12
    c.setFont(B, 7.5); c.setFillColorRGB(0.35,0.35,0.35)
    esic_note = "ESIC not eligible if monthly Gross Salary is above Rs 21,000/-"
    for note in [
        f"1. {esic_note}",
        "2. TDS will be calculated as per the applicable provisions of the Income Tax Act, 1961.",
        "   Deduction based on tax regime chosen (Old or New) and investment declarations made during the financial year.",
        "3. Health insurance amount is approximate and subject to change after submission of family member documents.",
    ]:
        c.drawString(M, y, note); y -= 11


# ── PDF dispatcher ────────────────────────────────────────────────────────────
PDF_BUILDERS = {
    "classic":   pdf_classic,
    "modern":    pdf_modern,
    "minimal":   pdf_minimal,
    "corporate": pdf_corporate,
}

def build_pdf(d, name, desig, dept, eid, tmpl, hdr, acc, txt, font, company):
    return PDF_BUILDERS[tmpl](d, name, desig, dept, eid, hdr, acc, txt, font, company)


# ── Trigger ───────────────────────────────────────────────────────────────────
if calc_btn and net_input:
    st.session_state["d"]       = calc_ctc(int(net_input))
    st.session_state["name"]    = emp_name
    st.session_state["desig"]   = emp_desig
    st.session_state["dept"]    = emp_dept
    st.session_state["eid"]     = emp_id
    st.session_state["hdr"]     = custom_header
    st.session_state["acc"]     = custom_accent
    st.session_state["txt"]     = custom_text
    st.session_state["font"]    = font_choice
    st.session_state["company"] = show_logo_text

# ── Render ────────────────────────────────────────────────────────────────────
if "d" in st.session_state:
    d       = st.session_state["d"]
    name    = st.session_state["name"]
    desig   = st.session_state["desig"]
    dept    = st.session_state.get("dept","")
    eid     = st.session_state.get("eid","")
    hdr     = st.session_state.get("hdr", custom_header)
    acc     = st.session_state.get("acc", custom_accent)
    txt_c   = st.session_state.get("txt", custom_text)
    font    = st.session_state.get("font", font_choice)
    company = st.session_state.get("company", show_logo_text)
    tmpl    = st.session_state["template"]

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

    table_row(cw, "Basic Salary",                    "Fully Taxable", d["basic"],      d["basic"]*12)
    table_row(cw, "House Rent Allowance",            "Fully Taxable", d["hra"],        d["hra"]*12)
    table_row(cw, "Statutory Bonus",                 "Fully Taxable", d["stat_bonus"], d["stat_bonus"]*12)
    table_row(cw, "Conveyance / Transport Allowance","Fully Taxable", d["conveyance"], d["conveyance"]*12)
    st.markdown(f"<div class='grand-total'>Total Gross Salary (A) &nbsp;|&nbsp; {fmt(d['total_gross'])} / mo &nbsp;|&nbsp; {fmt(d['total_gross']*12)} / yr</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Employer Contributions & Perquisites</div>", unsafe_allow_html=True)
    table_row(cw, "PF employer contribution",        "Employer rate 12% of 15000", d["pf_ec"], d["pf_ec"]*12)
    table_row(cw, "ESIC employer contribution",
        "Employer rate 3.25%" if d["esic_eligible"] else "Not Eligible",
        d["esic_emp_amt"] if d["esic_eligible"] else None,
        d["esic_emp_amt"]*12 if d["esic_eligible"] else None)
    table_row(cw, "Gratuity employer contribution",  "Gratuity rate 4.81%", d["gratuity"], d["gratuity"]*12)
    table_row(cw, "Employee Health Insurance",       "Fully Taxable",       d["health_ins"], d["health_ins"]*12)
    st.markdown(f"<div class='grand-total'>Total Employer Contributions & Perquisites (B) &nbsp;|&nbsp; {fmt(d['total_ec'])} / mo &nbsp;|&nbsp; {fmt(d['total_ec']*12)} / yr</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='grand-total'>Total CTC Fixed (A+B) (C) &nbsp;|&nbsp; {fmt(d['total_ctc'])} / mo &nbsp;|&nbsp; {fmt(d['total_ctc']*12)} / yr</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>PLI / Bonus / Variable Pay</div>", unsafe_allow_html=True)
    table_row(cw, "Performance Pay", "Subject to Performance Review", None, None)
    st.markdown(f"<div class='grand-total'>Total CTC Including Variable (D) &nbsp;|&nbsp; Annual: {fmt(d['total_ctc']*12)}</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Employee Contributions</div>", unsafe_allow_html=True)
    table_row(cw, "PF employee contribution",  "Employee rate 12% of 15000", d["pf_emp"], d["pf_emp"]*12)
    table_row(cw, "ESIC employee contribution",
        "Employee rate 0.75%" if d["esic_eligible"] else "Not Eligible",
        d["esic_emp_amt2"] if d["esic_eligible"] else None,
        d["esic_emp_amt2"]*12 if d["esic_eligible"] else None)
    table_row(cw, "Professional Tax", "NA", None, None)
    table_row(cw, "Total Employee Contributions (E)", "", d["total_ded"], d["total_ded"]*12, bold=True)
    st.markdown(f"<div class='net-total'>Net Take Home Before TDS (A−E) &nbsp;|&nbsp; {fmt(d['net_take_home'])} / mo &nbsp;|&nbsp; {fmt(d['net_take_home']*12)} / yr</div>", unsafe_allow_html=True)

    st.divider()
    esic_note = f"ESIC {'applicable' if d['esic_eligible'] else 'not applicable'} — gross ₹{d['gross']:,.0f} is {'below' if d['esic_eligible'] else 'above'} ₹21,000."
    st.info(f"**Notes:** {esic_note} | TDS per Income Tax Act 1961. | Health insurance approximate.")

    # Download
    st.markdown(f"**Downloading:** `{TEMPLATES[tmpl]['name']}` template")
    pdf_buf  = build_pdf(d, name, desig, dept, eid, tmpl, hdr, acc, txt_c, font, company)
    fname    = f"CTC_{(name or 'Employee').replace(' ','_')}_{tmpl}.pdf"
    st.download_button(
        label=f"⬇️ Download PDF — {TEMPLATES[tmpl]['name']} Template",
        data=pdf_buf,
        file_name=fname,
        mime="application/pdf",
        use_container_width=True,
        type="primary"
    )
