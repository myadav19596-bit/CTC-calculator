import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

st.set_page_config(
    page_title="CTC Structure Generator",
    page_icon="💼",
    layout="centered"
)

st.markdown("""
<style>
    .block-container { max-width: 760px; padding-top: 2rem; }
    .section-title {
        background: #eef2f7;
        padding: 6px 12px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.83rem;
        color: #555;
        margin: 10px 0 4px 0;
    }
    .grand-total {
        background: #dce8f7;
        padding: 8px 14px;
        border-radius: 6px;
        font-weight: 600;
        color: #1a5fa8;
        margin: 4px 0;
    }
    .net-total {
        background: #d4edda;
        padding: 8px 14px;
        border-radius: 6px;
        font-weight: 600;
        color: #2d7a3a;
        margin: 4px 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("💼 CTC Structure Generator")
st.caption("Enter net take-home salary to auto-calculate the full CTC structure")

# ── Inputs ────────────────────────────────────────────────────────────────────
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

calc_btn = st.button("🔢 Calculate CTC Structure", type="primary", use_container_width=True)


# ── Calculation ───────────────────────────────────────────────────────────────
def calc_ctc(net_monthly):
    pf_emp = 1800
    gross  = net_monthly + pf_emp

    esic_eligible = gross < 21000
    esic_emp_amt  = round(gross * 0.0325) if esic_eligible else 0
    esic_emp_amt2 = round(gross * 0.0075) if esic_eligible else 0

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


# ── PDF builder ───────────────────────────────────────────────────────────────
def build_pdf(d, name, desig):
    buf = io.BytesIO()
    c   = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    M = 40
    y = H - 50

    def fp(n):
        return "-" if n is None else f"{n:,.2f}"

    CX = [M, 270, 390, 490]
    CW = [230, 110, 100, 95]

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(W / 2, y, "CTC Salary Annexure - 1")
    y -= 18
    c.setFont("Helvetica", 11)
    c.drawCentredString(W / 2, y, (name or "Employee") + (f"  |  {desig}" if desig else ""))
    y -= 24

    c.setFillColorRGB(0.90, 0.94, 0.98)
    c.rect(M, y - 4, W - M * 2, 18, fill=1, stroke=0)
    c.setFillColorRGB(0.09, 0.37, 0.65)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(CX[0] + 4, y + 8, "Fixed Allowance Type")
    c.drawString(CX[1] + 4, y + 8, "Type")
    c.drawRightString(CX[2] + CW[2], y + 8, "Monthly Amt")
    c.drawRightString(CX[3] + CW[3], y + 8, "Yearly Amt")
    c.setFillColorRGB(0, 0, 0)
    y -= 20

    def pr(label, typ, mo, yr, kind="normal"):
        nonlocal y
        rh = 16

        if kind == "section":
            c.setFillColorRGB(0.94, 0.96, 0.98)
            c.rect(M, y - 4, W - M * 2, rh, fill=1, stroke=0)
            c.setFillColorRGB(0.31, 0.31, 0.39)
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(CX[0] + 4, y + 7, label)
            c.setFillColorRGB(0, 0, 0)
            y -= rh
            return

        if kind == "grand":
            c.setFillColorRGB(0.82, 0.89, 0.97)
            c.rect(M, y - 4, W - M * 2, 20, fill=1, stroke=0)
            c.setFillColorRGB(0.05, 0.27, 0.49)
            c.setFont("Helvetica-Bold", 9.5)
            c.drawString(CX[0] + 4, y + 9, label)
            if mo is not None: c.drawRightString(CX[2] + CW[2], y + 9, fp(mo))
            if yr is not None: c.drawRightString(CX[3] + CW[3], y + 9, fp(yr))
            c.setFillColorRGB(0, 0, 0)
            y -= 22
            return

        if kind == "net":
            c.setFillColorRGB(0.82, 0.94, 0.84)
            c.rect(M, y - 4, W - M * 2, 20, fill=1, stroke=0)
            c.setFillColorRGB(0.12, 0.39, 0.16)
            c.setFont("Helvetica-Bold", 9.5)
            c.drawString(CX[0] + 4, y + 9, label)
            c.drawRightString(CX[2] + CW[2], y + 9, fp(mo))
            c.drawRightString(CX[3] + CW[3], y + 9, fp(yr))
            c.setFillColorRGB(0, 0, 0)
            y -= 22
            return

        if kind == "total":
            c.setFillColorRGB(0.86, 0.92, 0.98)
            c.rect(M, y - 4, W - M * 2, rh, fill=1, stroke=0)
            c.setFont("Helvetica-Bold", 9)
        else:
            c.setFont("Helvetica", 9)

        c.setFillColorRGB(0, 0, 0)
        c.drawString(CX[0] + 4, y + 7, label)
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.35, 0.35, 0.35)
        if typ: c.drawString(CX[1] + 4, y + 7, typ)
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold" if kind == "total" else "Helvetica", 9)
        c.drawRightString(CX[2] + CW[2], y + 7, fp(mo))
        c.drawRightString(CX[3] + CW[3], y + 7, fp(yr))
        c.setStrokeColorRGB(0.82, 0.87, 0.90)
        c.line(M, y - 4, W - M, y - 4)
        y -= rh

    pr("Basic Salary",                     "Fully Taxable",                       d["basic"],      d["basic"] * 12)
    pr("House Rent Allowance",             "Fully Taxable",                       d["hra"],        d["hra"] * 12)
    pr("Statutory Bonus",                  "Fully Taxable",                       d["stat_bonus"], d["stat_bonus"] * 12)
    pr("Conveyance / Transport Allowance", "Fully Taxable",                       d["conveyance"], d["conveyance"] * 12)
    pr("Total Gross Salary (A)",           "",                                    d["total_gross"],d["total_gross"] * 12, "total")
    pr("Employer Contributions & Perquisites", "", None, None, "section")
    pr("PF employer contribution",         "Employer rate 12% of 15000",          d["pf_ec"],      d["pf_ec"] * 12)
    pr("ESIC employer contribution",
       "Employer rate 3.25%" if d["esic_eligible"] else "Not Eligible",
       d["esic_emp_amt"] if d["esic_eligible"] else None,
       d["esic_emp_amt"] * 12 if d["esic_eligible"] else None)
    pr("Gratuity employer contribution",   "Gratuity rate 4.81%",                 d["gratuity"],   d["gratuity"] * 12)
    pr("Employee Health Insurance",        "Fully Taxable",                       d["health_ins"], d["health_ins"] * 12)
    pr("Total Employer Contributions & Perquisites (B)", "",                      d["total_ec"],   d["total_ec"] * 12, "total")
    pr("Total CTC (Fixed) (A+B) (C)",     "",                                    d["total_ctc"],  d["total_ctc"] * 12, "grand")
    pr("PLI / Bonus / Variable Pay",       "", None, None, "section")
    pr("Performance Pay",                  "Subject to Performance Review & paid annually", None, None)
    pr("Total CTC (Including Variable) (D)", "",                                  d["total_ctc"],  d["total_ctc"] * 12, "grand")
    pr("Employee Contributions",           "", None, None, "section")
    pr("PF employee contribution",         "Employee rate 12% of 15000",          d["pf_emp"],     d["pf_emp"] * 12)
    pr("ESIC employee contribution",
       "Employee rate 0.75%" if d["esic_eligible"] else "Not Eligible",
       d["esic_emp_amt2"] if d["esic_eligible"] else None,
       d["esic_emp_amt2"] * 12 if d["esic_eligible"] else None)
    pr("Professional Tax",                 "NA",                                  None,            None)
    pr("Total Employee Contributions (E)", "",                                    d["total_ded"],  d["total_ded"] * 12, "total")
    pr("Net Take Home (Before TDS) (A-E)","",                                    d["net_take_home"], d["net_take_home"] * 12, "net")

    y -= 12
    c.setFont("Helvetica-Bold", 8)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(M, y, "Note:")
    y -= 14
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.24, 0.24, 0.24)
    for note in [
        "1. ESIC not eligible if monthly Gross Salary is above Rs 21,000/-",
        "2. TDS calculated per Income Tax Act 1961 based on chosen regime (Old/New) and investment declarations.",
        "3. Health insurance amount is approximate and subject to change after submission of family documents.",
    ]:
        c.drawString(M, y, note)
        y -= 13

    c.save()
    buf.seek(0)
    return buf


# ── Trigger ───────────────────────────────────────────────────────────────────
if calc_btn and net_input:
    st.session_state["d"]     = calc_ctc(int(net_input))
    st.session_state["name"]  = emp_name
    st.session_state["desig"] = emp_desig

# ── Display ───────────────────────────────────────────────────────────────────
if "d" in st.session_state:
    d     = st.session_state["d"]
    name  = st.session_state["name"]
    desig = st.session_state["desig"]

    st.divider()
    if name:
        st.subheader(f"📄 {name}" + (f" — {desig}" if desig else ""))

    m1, m2, m3 = st.columns(3)
    m1.metric("Monthly CTC",   fmt(d["total_ctc"]))
    m2.metric("Annual CTC",    fmt(d["total_ctc"] * 12))
    m3.metric("Net Take-Home", fmt(d["net_take_home"]))

    st.divider()

    cw = [4, 2.5, 1.8, 1.8]
    h  = st.columns(cw)
    h[0].markdown("**Component**")
    h[1].markdown("**Type**")
    h[2].markdown("**Monthly**")
    h[3].markdown("**Yearly**")
    st.markdown("---")

    table_row(cw, "Basic Salary",                    "Fully Taxable", d["basic"],      d["basic"] * 12)
    table_row(cw, "House Rent Allowance",            "Fully Taxable", d["hra"],        d["hra"] * 12)
    table_row(cw, "Statutory Bonus",                 "Fully Taxable", d["stat_bonus"], d["stat_bonus"] * 12)
    table_row(cw, "Conveyance / Transport Allowance","Fully Taxable", d["conveyance"], d["conveyance"] * 12)

    st.markdown(f"<div class='grand-total'>Total Gross Salary (A) &nbsp;|&nbsp; {fmt(d['total_gross'])} / mo &nbsp;|&nbsp; {fmt(d['total_gross']*12)} / yr</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Employer Contributions & Perquisites</div>", unsafe_allow_html=True)

    table_row(cw, "PF employer contribution",        "Employer rate 12% of 15000", d["pf_ec"], d["pf_ec"] * 12)
    table_row(cw, "ESIC employer contribution",
        "Employer rate 3.25%" if d["esic_eligible"] else "Not Eligible",
        d["esic_emp_amt"] if d["esic_eligible"] else None,
        d["esic_emp_amt"] * 12 if d["esic_eligible"] else None)
    table_row(cw, "Gratuity employer contribution",  "Gratuity rate 4.81%", d["gratuity"],   d["gratuity"] * 12)
    table_row(cw, "Employee Health Insurance",       "Fully Taxable",       d["health_ins"], d["health_ins"] * 12)

    st.markdown(f"<div class='grand-total'>Total Employer Contributions & Perquisites (B) &nbsp;|&nbsp; {fmt(d['total_ec'])} / mo &nbsp;|&nbsp; {fmt(d['total_ec']*12)} / yr</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='grand-total'>Total CTC Fixed (A+B) (C) &nbsp;|&nbsp; {fmt(d['total_ctc'])} / mo &nbsp;|&nbsp; {fmt(d['total_ctc']*12)} / yr</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>PLI / Bonus / Variable Pay</div>", unsafe_allow_html=True)
    table_row(cw, "Performance Pay", "Subject to Performance Review", None, None)
    st.markdown(f"<div class='grand-total'>Total CTC Including Variable (D) &nbsp;|&nbsp; Annual: {fmt(d['total_ctc']*12)}</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>Employee Contributions</div>", unsafe_allow_html=True)
    table_row(cw, "PF employee contribution",  "Employee rate 12% of 15000", d["pf_emp"], d["pf_emp"] * 12)
    table_row(cw, "ESIC employee contribution",
        "Employee rate 0.75%" if d["esic_eligible"] else "Not Eligible",
        d["esic_emp_amt2"] if d["esic_eligible"] else None,
        d["esic_emp_amt2"] * 12 if d["esic_eligible"] else None)
    table_row(cw, "Professional Tax", "NA", None, None)
    table_row(cw, "Total Employee Contributions (E)", "", d["total_ded"], d["total_ded"] * 12, bold=True)

    st.markdown(f"<div class='net-total'>Net Take Home Before TDS (A−E) &nbsp;|&nbsp; {fmt(d['net_take_home'])} / mo &nbsp;|&nbsp; {fmt(d['net_take_home']*12)} / yr</div>", unsafe_allow_html=True)

    st.divider()

    esic_note = f"ESIC {'applicable' if d['esic_eligible'] else 'not applicable'} — gross ₹{d['gross']:,.0f} is {'below' if d['esic_eligible'] else 'above'} ₹21,000."
    st.info(f"""**Notes:**
1. {esic_note}
2. TDS deducted as per Income Tax Act, 1961 based on chosen regime (Old/New).
3. Health insurance amount approximate — subject to change after document submission.""")

    # Build PDF into BytesIO and pass directly to st.download_button
    pdf_buf  = build_pdf(d, name, desig)
    fname    = f"CTC_{(name or 'Employee').replace(' ', '_')}.pdf"

    st.download_button(
        label="⬇️ Download PDF",
        data=pdf_buf,
        file_name=fname,
        mime="application/pdf",
        use_container_width=True,
        type="primary"
    )
