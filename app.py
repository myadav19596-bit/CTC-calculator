import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import io
import math

st.set_page_config(page_title="CTC Structure Generator", page_icon="💼", layout="centered")

st.markdown("""
<style>
    .main { max-width: 750px; }
    .stButton > button { width: 100%; }
    div[data-testid="stMetricValue"] { font-size: 1.4rem; }
    .section-title { 
        background: #f0f4f8; 
        padding: 6px 12px; 
        border-radius: 6px; 
        font-weight: 600; 
        font-size: 0.85rem;
        color: #444;
        margin: 8px 0 4px 0;
    }
    .grand-total {
        background: #dce8f7;
        padding: 8px 12px;
        border-radius: 6px;
        font-weight: 600;
        color: #1a5fa8;
    }
    .net-total {
        background: #d4edda;
        padding: 8px 12px;
        border-radius: 6px;
        font-weight: 600;
        color: #2d7a3a;
    }
</style>
""", unsafe_allow_html=True)

st.title("💼 CTC Structure Generator")
st.caption("Enter net take-home salary to auto-calculate the full CTC structure")

# ── Inputs ──────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    emp_name = st.text_input("Employee Name", placeholder="e.g. Rahul Sharma")
with col2:
    emp_desig = st.text_input("Designation", placeholder="e.g. Software Engineer")

net_input = st.number_input(
    "Net Take-Home Salary (Monthly ₹)",
    min_value=1000,
    max_value=10000000,
    value=None,
    step=500,
    placeholder="e.g. 69000",
    format="%d"
)

calculate = st.button("🔢 Calculate CTC Structure", type="primary", use_container_width=True)


# ── Calculation logic ────────────────────────────────────────────────────────
def calc_ctc(net_monthly):
    pf_emp = 1800  # 12% of 15000

    gross = net_monthly + pf_emp

    # ESIC only if gross < 21000
    esic_eligible = gross < 21000
    esic_emp_amt  = round(gross * 0.0325) if esic_eligible else 0
    esic_emp_amt2 = round(gross * 0.0075) if esic_eligible else 0

    # CTC = (Gross + 2300 + esic_emp_amt) / (1 - 0.02405)
    # Basic = 50% CTC | HRA = 50% Basic | StatBonus = 15% Basic (no gross limit)
    # Gratuity = 4.81% Basic | Health = 500 fixed | PF employer = 1800
    ctc        = (gross + 2300 + esic_emp_amt) / (1 - 0.02405)
    basic      = round(ctc * 0.5)
    hra        = round(basic * 0.5)
    stat_bonus = round(basic * 0.15)
    conveyance = gross - basic - hra - stat_bonus
    gratuity   = round(basic * 0.0481)
    health_ins = 500
    pf_emp_contrib = 1800

    total_gross       = basic + hra + stat_bonus + conveyance
    total_emp_contrib = pf_emp_contrib + esic_emp_amt + gratuity + health_ins
    total_ctc         = total_gross + total_emp_contrib
    total_emp_deduct  = pf_emp + esic_emp_amt2
    net_take_home     = total_gross - total_emp_deduct

    return {
        "basic": basic, "hra": hra, "stat_bonus": stat_bonus, "conveyance": conveyance,
        "total_gross": total_gross,
        "pf_emp_contrib": pf_emp_contrib, "esic_emp_amt": esic_emp_amt,
        "gratuity": gratuity, "health_ins": health_ins,
        "total_emp_contrib": total_emp_contrib,
        "total_ctc": total_ctc,
        "pf_emp": pf_emp, "esic_emp_amt2": esic_emp_amt2,
        "total_emp_deduct": total_emp_deduct,
        "net_take_home": net_take_home,
        "esic_eligible": esic_eligible,
        "gross": gross
    }


def fmt(n):
    if n is None:
        return "-"
    return f"₹{n:,.2f}"


def render_row(col_widths, label, typ, monthly, yearly, bold=False):
    cols = st.columns(col_widths)
    style = "**" if bold else ""
    cols[0].markdown(f"{style}{label}{style}")
    cols[1].markdown(f"<small style='color:#777'>{typ}</small>", unsafe_allow_html=True)
    cols[2].markdown(f"{style}{fmt(monthly)}{style}")
    cols[3].markdown(f"{style}{fmt(yearly)}{style}")


# ── PDF Generator ─────────────────────────────────────────────────────────────
def generate_pdf(d, emp_name, emp_desig):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    margin = 40
    y = H - 50

    def fmtp(n):
        if n is None:
            return "-"
        return f"{n:,.2f}"

    COL = [margin, 270, 390, 490]
    CW  = [230, 110, 100, 95]

    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(W / 2, y, "CTC Salary Annexure - 1")
    y -= 18
    c.setFont("Helvetica", 11)
    info = emp_name or "Employee"
    if emp_desig:
        info += f"  |  {emp_desig}"
    c.drawCentredString(W / 2, y, info)
    y -= 22

    # Header row
    c.setFillColorRGB(0.9, 0.94, 0.98)
    c.rect(margin, y - 4, W - margin * 2, 18, fill=1, stroke=0)
    c.setFillColorRGB(0.09, 0.37, 0.65)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(COL[0] + 4, y + 8, "Fixed Allowance Type")
    c.drawString(COL[1] + 4, y + 8, "Type")
    c.drawRightString(COL[2] + CW[2], y + 8, "Monthly Amt")
    c.drawRightString(COL[3] + CW[3], y + 8, "Yearly Amt")
    c.setFillColorRGB(0, 0, 0)
    y -= 18

    def pdf_row(label, typ, monthly, yearly, kind="normal"):
        nonlocal y
        rh = 16

        if kind == "section":
            c.setFillColorRGB(0.94, 0.96, 0.98)
            c.rect(margin, y - 4, W - margin * 2, rh, fill=1, stroke=0)
            c.setFillColorRGB(0.31, 0.31, 0.39)
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(COL[0] + 4, y + 7, label)
            c.setFillColorRGB(0, 0, 0)
            y -= rh
            return

        if kind == "grand":
            c.setFillColorRGB(0.82, 0.89, 0.97)
            c.rect(margin, y - 4, W - margin * 2, 20, fill=1, stroke=0)
            c.setFillColorRGB(0.05, 0.27, 0.49)
            c.setFont("Helvetica-Bold", 9.5)
            c.drawString(COL[0] + 4, y + 9, label)
            if monthly is not None:
                c.drawRightString(COL[2] + CW[2], y + 9, fmtp(monthly))
            if yearly is not None:
                c.drawRightString(COL[3] + CW[3], y + 9, fmtp(yearly))
            c.setFillColorRGB(0, 0, 0)
            y -= 22
            return

        if kind == "net":
            c.setFillColorRGB(0.82, 0.94, 0.84)
            c.rect(margin, y - 4, W - margin * 2, 20, fill=1, stroke=0)
            c.setFillColorRGB(0.12, 0.39, 0.16)
            c.setFont("Helvetica-Bold", 9.5)
            c.drawString(COL[0] + 4, y + 9, label)
            c.drawRightString(COL[2] + CW[2], y + 9, fmtp(monthly))
            c.drawRightString(COL[3] + CW[3], y + 9, fmtp(yearly))
            c.setFillColorRGB(0, 0, 0)
            y -= 22
            return

        if kind == "total":
            c.setFillColorRGB(0.86, 0.92, 0.98)
            c.rect(margin, y - 4, W - margin * 2, rh, fill=1, stroke=0)
            c.setFont("Helvetica-Bold", 9)
        else:
            c.setFont("Helvetica", 9)

        c.setFillColorRGB(0, 0, 0)
        c.drawString(COL[0] + 4, y + 7, label)
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.31, 0.31, 0.31)
        if typ:
            c.drawString(COL[1] + 4, y + 7, typ)
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold" if kind == "total" else "Helvetica", 9)
        c.drawRightString(COL[2] + CW[2], y + 7, fmtp(monthly))
        c.drawRightString(COL[3] + CW[3], y + 7, fmtp(yearly))
        c.setStrokeColorRGB(0.82, 0.87, 0.90)
        c.line(margin, y - 4, W - margin, y - 4)
        y -= rh

    pdf_row("Basic Salary", "Fully Taxable", d["basic"], d["basic"] * 12)
    pdf_row("House Rent Allowance", "Fully Taxable", d["hra"], d["hra"] * 12)
    pdf_row("Statutory Bonus", "Fully Taxable", d["stat_bonus"], d["stat_bonus"] * 12)
    pdf_row("Conveyance / Transport Allowance", "Fully Taxable", d["conveyance"], d["conveyance"] * 12)
    pdf_row("Total Gross Salary (A)", "", d["total_gross"], d["total_gross"] * 12, "total")
    pdf_row("Employer Contributions & Perquisites", "", None, None, "section")
    pdf_row("PF employer contribution", "Employer rate 12% of 15000", d["pf_emp_contrib"], d["pf_emp_contrib"] * 12)
    esic_type = "Employer rate 3.25%" if d["esic_eligible"] else "Not Eligible"
    pdf_row("ESIC employer contribution", esic_type,
            d["esic_emp_amt"] if d["esic_eligible"] else None,
            d["esic_emp_amt"] * 12 if d["esic_eligible"] else None)
    pdf_row("Gratuity employer contribution", "Gratuity rate 4.81%", d["gratuity"], d["gratuity"] * 12)
    pdf_row("Employee Health Insurance", "Fully Taxable", d["health_ins"], d["health_ins"] * 12)
    pdf_row("Total Employer Contributions & Perquisites (B)", "", d["total_emp_contrib"], d["total_emp_contrib"] * 12, "total")
    pdf_row("Total CTC (Fixed) (A+B) (C)", "", d["total_ctc"], d["total_ctc"] * 12, "grand")
    pdf_row("PLI/Bonus/Variable Pay", "", None, None, "section")
    pdf_row("Performance Pay", "Subject to Performance Review & paid annually", None, None)
    pdf_row("Total CTC (Including Variable) (D)", "", d["total_ctc"], d["total_ctc"] * 12, "grand")
    pdf_row("Employee Contributions", "", None, None, "section")
    pdf_row("PF employee contribution", "Employee rate 12% of 15000", d["pf_emp"], d["pf_emp"] * 12)
    esic_emp_type = "Employee rate 0.75%" if d["esic_eligible"] else "Not Eligible"
    pdf_row("ESIC employee contribution", esic_emp_type,
            d["esic_emp_amt2"] if d["esic_eligible"] else None,
            d["esic_emp_amt2"] * 12 if d["esic_eligible"] else None)
    pdf_row("Professional Tax", "NA", None, None)
    pdf_row("Total Employee Contributions (E)", "", d["total_emp_deduct"], d["total_emp_deduct"] * 12, "total")
    pdf_row("Net Take Home (Before TDS) (A-E)", "", d["net_take_home"], d["net_take_home"] * 12, "net")

    # Notes
    y -= 10
    c.setFont("Helvetica-Bold", 8)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(margin, y, "Note:")
    y -= 14
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.24, 0.24, 0.24)
    notes = [
        "1. ESIC not eligible if monthly Gross Salary is above Rs 21,000/-",
        "2. TDS will be calculated as per the applicable provisions of the Income Tax Act, 1961, and will be deducted",
        "   from your monthly salary accordingly. The deduction will be based on the tax regime chosen by you (Old or",
        "   New) and the investment declarations made during the financial year.",
        "3. The amount mentioned for health insurance in your CTC is approximate and is subject to change. The final",
        "   premium will be determined after submission of your family members' documents and required health declarations."
    ]
    for note in notes:
        c.drawString(margin, y, note)
        y -= 13

    c.save()
    buf.seek(0)
    return buf


# ── Main display ──────────────────────────────────────────────────────────────
if calculate and net_input:
    d = calc_ctc(int(net_input))
    st.session_state["ctc_data"] = d
    st.session_state["emp_name"] = emp_name
    st.session_state["emp_desig"] = emp_desig

if "ctc_data" in st.session_state:
    d = st.session_state["ctc_data"]
    name = st.session_state.get("emp_name", "")
    desig = st.session_state.get("emp_desig", "")

    st.divider()
    if name:
        st.subheader(f"📄 CTC Structure — {name}" + (f" ({desig})" if desig else ""))

    # Summary metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Monthly CTC", fmt(d["total_ctc"]))
    m2.metric("Annual CTC", fmt(d["total_ctc"] * 12))
    m3.metric("Net Take-Home", fmt(d["net_take_home"]))

    st.divider()

    # Table header
    cw = [4, 2.5, 1.8, 1.8]
    hcols = st.columns(cw)
    hcols[0].markdown("**Component**")
    hcols[1].markdown("**Type**")
    hcols[2].markdown("**Monthly**")
    hcols[3].markdown("**Yearly**")
    st.markdown("---")

    # Fixed allowances
    render_row(cw, "Basic Salary", "Fully Taxable", d["basic"], d["basic"] * 12)
    render_row(cw, "House Rent Allowance", "Fully Taxable", d["hra"], d["hra"] * 12)
    render_row(cw, "Statutory Bonus", "Fully Taxable", d["stat_bonus"], d["stat_bonus"] * 12)
    render_row(cw, "Conveyance / Transport Allowance", "Fully Taxable", d["conveyance"], d["conveyance"] * 12)

    st.markdown(f"<div class='grand-total'>Total Gross Salary (A) &nbsp;&nbsp;&nbsp; {fmt(d['total_gross'])} / month &nbsp;&nbsp;&nbsp; {fmt(d['total_gross']*12)} / year</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Employer Contributions & Perquisites</div>", unsafe_allow_html=True)

    render_row(cw, "PF employer contribution", "Employer rate 12% of 15000", d["pf_emp_contrib"], d["pf_emp_contrib"] * 12)
    esic_type = "Employer rate 3.25%" if d["esic_eligible"] else "Not Eligible"
    render_row(cw, "ESIC employer contribution", esic_type,
               d["esic_emp_amt"] if d["esic_eligible"] else None,
               d["esic_emp_amt"] * 12 if d["esic_eligible"] else None)
    render_row(cw, "Gratuity employer contribution", "Gratuity rate 4.81%", d["gratuity"], d["gratuity"] * 12)
    render_row(cw, "Employee Health Insurance", "Fully Taxable", d["health_ins"], d["health_ins"] * 12)

    st.markdown(f"<div class='grand-total'>Total Employer Contributions & Perquisites (B) &nbsp;&nbsp;&nbsp; {fmt(d['total_emp_contrib'])} / month &nbsp;&nbsp;&nbsp; {fmt(d['total_emp_contrib']*12)} / year</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='grand-total' style='margin-top:6px'>Total CTC Fixed (A+B) (C) &nbsp;&nbsp;&nbsp; {fmt(d['total_ctc'])} / month &nbsp;&nbsp;&nbsp; {fmt(d['total_ctc']*12)} / year</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>PLI / Bonus / Variable Pay</div>", unsafe_allow_html=True)
    render_row(cw, "Performance Pay", "Subject to Performance Review", None, None)
    st.markdown(f"<div class='grand-total'>Total CTC Including Variable (D) &nbsp;&nbsp;&nbsp; Annual: {fmt(d['total_ctc']*12)}</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>Employee Contributions</div>", unsafe_allow_html=True)
    render_row(cw, "PF employee contribution", "Employee rate 12% of 15000", d["pf_emp"], d["pf_emp"] * 12)
    esic_emp_type = "Employee rate 0.75%" if d["esic_eligible"] else "Not Eligible"
    render_row(cw, "ESIC employee contribution", esic_emp_type,
               d["esic_emp_amt2"] if d["esic_eligible"] else None,
               d["esic_emp_amt2"] * 12 if d["esic_eligible"] else None)
    render_row(cw, "Professional Tax", "NA", None, None)
    render_row(cw, "Total Employee Contributions (E)", "", d["total_emp_deduct"], d["total_emp_deduct"] * 12, bold=True)

    st.markdown(f"<div class='net-total'>Net Take Home (Before TDS) (A−E) &nbsp;&nbsp;&nbsp; {fmt(d['net_take_home'])} / month &nbsp;&nbsp;&nbsp; {fmt(d['net_take_home']*12)} / year</div>", unsafe_allow_html=True)

    st.divider()

    # Notes
    esic_note = f"ESIC {'applicable' if d['esic_eligible'] else 'not eligible'} — monthly gross ₹{d['gross']:,.0f} is {'below' if d['esic_eligible'] else 'above'} ₹21,000."
    st.info(f"""
**Notes:**
1. {esic_note}
2. TDS will be calculated as per the Income Tax Act, 1961 based on your chosen regime (Old or New).
3. Health insurance amount is approximate and subject to change after document submission.
    """)

    # PDF download
    pdf_buf = generate_pdf(d, name, desig)
    fname = f"CTC_Structure_{name.replace(' ','_') or 'Employee'}.pdf"
    st.download_button(
        label="⬇️ Download PDF",
        data=pdf_buf,
        file_name=fname,
        mime="application/pdf",
        use_container_width=True,
        type="primary"
    )
