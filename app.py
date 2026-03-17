import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io, datetime

st.set_page_config(page_title="CTC Structure Generator", page_icon="💼", layout="centered")

st.markdown("""
<style>
    .block-container { max-width: 780px; padding-top: 2rem; }
    .section-title { background:#eef2f7; padding:6px 12px; border-radius:6px; font-weight:600; font-size:0.83rem; color:#555; margin:10px 0 4px 0; }
    .grand-total  { background:#dce8f7; padding:8px 14px; border-radius:6px; font-weight:600; color:#1a5fa8; margin:4px 0; }
    .net-total    { background:#d4edda; padding:8px 14px; border-radius:6px; font-weight:600; color:#2d7a3a; margin:4px 0; }
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

c5, c6 = st.columns(2)
with c5:
    net_input = st.number_input(
        "Net Take-Home Salary (Monthly ₹)",
        min_value=1000, max_value=10000000, value=None,
        step=500, placeholder="e.g. 69000", format="%d"
    )
with c6:
    company_name = st.text_input("Company Name (optional)", placeholder="e.g. Acme Pvt. Ltd.")

# ── PF Option ─────────────────────────────────────────────────────────────────
st.markdown("#### 🔧 PF Calculation Basis")
pf_basis = st.radio(
    "Calculate PF (Employer & Employee) on:",
    options=["12% of ₹15,000 (capped) = ₹1,800 fixed", "12% of Basic Salary (actual)"],
    index=0,
    horizontal=True,
    help="Statutory minimum is 12% of ₹15,000. Many companies contribute 12% of actual Basic."
)
pf_on_basic = pf_basis.startswith("12% of Basic")

calc_btn = st.button("🔢 Calculate CTC Structure", type="primary", use_container_width=True)


# ── Calculation ───────────────────────────────────────────────────────────────
def calc_ctc(net_monthly, pf_on_basic):
    # We need to solve for Basic algebraically because PF depends on Basic
    # when pf_on_basic=True.
    #
    # Definitions:
    #   Basic      = 0.5 * CTC
    #   HRA        = 0.5 * Basic
    #   StatBonus  = 0.15 * Basic
    #   Conveyance = Gross - Basic - HRA - StatBonus
    #   Gratuity   = 0.0481 * Basic
    #   Health     = 500
    #   PF         = 0.12 * Basic  (if pf_on_basic)  OR  1800 (fixed)
    #
    #   Gross          = Net + PF_employee
    #   CTC            = Gross + PF_employer + ESIC_employer + Gratuity + Health
    #   Basic          = 0.5 * CTC
    #
    # Case 1: PF fixed at 1800
    #   pf_emp = pf_ec = 1800
    #   gross  = net + 1800
    #   ESIC depends on gross
    #   CTC*(1-0.02405) = gross + 2300 + esic_emp_amt
    #
    # Case 2: PF = 12% of Basic
    #   pf_emp = pf_ec = 0.12 * Basic = 0.12 * 0.5 * CTC = 0.06 * CTC
    #   gross  = net + 0.06*CTC
    #   Gross  = Basic + HRA + StatBonus + Conveyance  =>  Gross is still net+pf_emp
    #   CTC    = Gross + pf_ec + esic_emp_amt + gratuity + health
    #          = Gross + 0.06*CTC + esic + 0.0481*0.5*CTC + 500
    #          = Gross + 0.06*CTC + esic + 0.02405*CTC + 500
    #   CTC*(1 - 0.06 - 0.02405) = Gross + esic + 500
    #   But Gross = net + 0.06*CTC  =>  substitute:
    #   CTC*(1 - 0.06 - 0.02405) = net + 0.06*CTC + esic + 500
    #   CTC*(1 - 0.06 - 0.02405 - 0.06) = net + esic + 500
    #   CTC*(0.85595) = net + esic + 500
    #   (ESIC depends on Gross which depends on CTC — iterate once since ESIC
    #    threshold is 21000 gross, we can check eligibility first without ESIC,
    #    then refine.)

    if not pf_on_basic:
        # ── Fixed PF ──────────────────────────────────────────────────────
        pf_fixed = 1800
        gross    = net_monthly + pf_fixed

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
        pf_ec      = pf_fixed
        pf_emp     = pf_fixed

        pf_label_ec  = "Employer rate 12% of 15000"
        pf_label_emp = "Employee rate 12% of 15000"

    else:
        # ── PF on Basic (12% of Basic) ────────────────────────────────────
        # First pass: estimate without ESIC to check eligibility
        # CTC*(0.85595) ≈ net + 500  (ignoring ESIC)
        ctc_est  = (net_monthly + 500) / 0.85595
        basic_est = ctc_est * 0.5
        gross_est = net_monthly + 0.12 * basic_est
        esic_eligible = gross_est < 21000

        # Second pass with ESIC if applicable
        # ESIC_emp = 3.25% * gross = 3.25% * (net + 0.06*CTC)
        # CTC*(1 - 0.06 - 0.02405 - 0.06) = net + esic + 500
        # With ESIC: esic = 0.0325 * (net + 0.06*CTC)
        #   CTC*(0.85595) = net + 0.0325*(net + 0.06*CTC) + 500
        #   CTC*(0.85595) = net*(1+0.0325) + 0.06*0.0325*CTC + 500
        #   CTC*(0.85595 - 0.001950) = net*1.0325 + 500
        #   CTC*0.853999 = net*1.0325 + 500
        if esic_eligible:
            ctc   = (net_monthly * 1.0325 + 500) / 0.854000
        else:
            ctc   = (net_monthly + 500) / 0.85595

        basic      = round(ctc * 0.50)
        hra        = round(basic * 0.50)
        stat_bonus = round(basic * 0.15)
        pf_ec      = round(basic * 0.12)
        pf_emp     = round(basic * 0.12)
        gross      = net_monthly + pf_emp
        conveyance = gross - basic - hra - stat_bonus
        gratuity   = round(basic * 0.0481)
        health_ins = 500

        esic_eligible = gross < 21000
        esic_emp_amt  = round(gross * 0.0325) if esic_eligible else 0
        esic_emp_amt2 = round(gross * 0.0075) if esic_eligible else 0

        pf_label_ec  = "Employer rate 12% of Basic"
        pf_label_emp = "Employee rate 12% of Basic"

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
        esic_eligible=esic_eligible, gross=gross,
        pf_label_ec=pf_label_ec, pf_label_emp=pf_label_emp,
        pf_on_basic=pf_on_basic,
    )


def fmt(n):
    return "-" if n is None else f"₹{n:,.2f}"

def nf(v):
    return "-" if v is None else f"{v:,.2f}"

def table_row(cw, label, typ, monthly, yearly, bold=False):
    cols = st.columns(cw)
    s = "**" if bold else ""
    cols[0].markdown(f"{s}{label}{s}")
    cols[1].markdown(f"<small style='color:#888'>{typ}</small>", unsafe_allow_html=True)
    cols[2].markdown(f"{s}{fmt(monthly)}{s}")
    cols[3].markdown(f"{s}{fmt(yearly)}{s}")


# ── PDF — Original template exact replica ─────────────────────────────────────
def build_pdf(d, name, desig, dept, eid, company):
    buf  = io.BytesIO()
    W, H = A4
    M    = 36
    c    = canvas.Canvas(buf, pagesize=A4)

    B  = "Times-Roman"
    BI = "Times-Bold"

    CX = [M, 230, 385, 488]
    CW = [194, 149, 97, 88]
    TW = W - M * 2

    y = H - 44

    # ── Employee info header ──────────────────────────────────────────────
    if any([company, name, desig, dept, eid]):
        if company:
            c.setFont(BI, 11); c.setFillColorRGB(0,0,0)
            c.drawString(M, y, company); y -= 14
        parts = [x for x in [name, desig, dept, f"ID: {eid}" if eid else ""] if x]
        if parts:
            c.setFont(B, 9); c.setFillColorRGB(0.2,0.2,0.2)
            c.drawString(M, y, "  |  ".join(parts)); y -= 12
        c.setFont(B, 8); c.setFillColorRGB(0.5,0.5,0.5)
        c.drawRightString(W-M, y, f"Date: {datetime.date.today().strftime('%d %b %Y')}")
        y -= 14

    table_top = y

    # ── Column header row ─────────────────────────────────────────────────
    c.setFillColorRGB(0.15,0.15,0.15)
    c.rect(M, y-18, TW, 18, fill=1, stroke=0)
    c.setFillColorRGB(1,1,1); c.setFont(BI, 9)
    c.drawString(CX[0]+4, y-11, "Fixed Allowance Type")
    c.drawString(CX[1]+4, y-11, "Type")
    c.drawRightString(CX[2]+CW[2], y-11, "Monthly Amt")
    c.drawRightString(CX[3]+CW[3], y-11, "Yearly Amt")
    c.setFillColorRGB(0,0,0); y -= 18

    ROW_H = 16; SEC_H = 14
    alt   = False

    def draw_row(label, typ, mo, yr,
                 is_section=False, is_total=False, is_grand=False, is_net=False,
                 row_alt=False):
        nonlocal y
        rh = SEC_H if is_section else ROW_H

        if is_grand:
            c.setFillColorRGB(0.82,0.89,0.97)
            c.rect(M, y-rh+2, TW, rh, fill=1, stroke=0)
        elif is_net:
            c.setFillColorRGB(0.78,0.92,0.80)
            c.rect(M, y-rh+2, TW, rh, fill=1, stroke=0)
        elif is_total:
            c.setFillColorRGB(0.88,0.88,0.88)
            c.rect(M, y-rh+2, TW, rh, fill=1, stroke=0)
        elif is_section:
            c.setFillColorRGB(0.93,0.93,0.93)
            c.rect(M, y-rh+2, TW, rh, fill=1, stroke=0)
        elif row_alt:
            c.setFillColorRGB(0.97,0.97,0.97)
            c.rect(M, y-rh+2, TW, rh, fill=1, stroke=0)

        bold = is_total or is_grand or is_net or is_section
        c.setFont(BI if bold else B, 8 if is_section else 8.5)

        ty = y - rh + 2 + rh * 0.52

        if is_grand:      c.setFillColorRGB(0.05,0.27,0.50)
        elif is_net:      c.setFillColorRGB(0.08,0.40,0.15)
        elif is_section:  c.setFillColorRGB(0.22,0.22,0.22)
        else:             c.setFillColorRGB(0,0,0)

        c.drawString(CX[0]+3, ty, label)

        if not is_section:
            c.setFont(B, 7.5); c.setFillColorRGB(0.38,0.38,0.38)
            if typ: c.drawString(CX[1]+3, ty, typ)
            if is_grand:   c.setFillColorRGB(0.05,0.27,0.50)
            elif is_net:   c.setFillColorRGB(0.08,0.40,0.15)
            else:          c.setFillColorRGB(0,0,0)
            c.setFont(BI if bold else B, 8.5)
            c.drawRightString(CX[2]+CW[2], ty, mo if mo else "-")
            c.drawRightString(CX[3]+CW[3], ty, yr if yr else "-")

        c.setStrokeColorRGB(0.72,0.72,0.72)
        c.setLineWidth(0.35)
        c.line(M, y-rh+2, M+TW, y-rh+2)
        y -= rh

    # ── Rows ──────────────────────────────────────────────────────────────
    draw_row("Basic Salary",                    "Fully Taxable",           nf(d["basic"]),      nf(d["basic"]*12),      row_alt=alt); alt=not alt
    draw_row("House Rent Allowance",            "Fully Taxable",           nf(d["hra"]),         nf(d["hra"]*12),        row_alt=alt); alt=not alt
    draw_row("Statutory Bonus",                 "Fully Taxable",           nf(d["stat_bonus"]),  nf(d["stat_bonus"]*12), row_alt=alt); alt=not alt
    draw_row("Conveyance/ Transport Allowance", "Fully Taxable",           nf(d["conveyance"]),  nf(d["conveyance"]*12), row_alt=alt); alt=not alt
    draw_row("Total Gross Salary (A)",          "",                        nf(d["total_gross"]), nf(d["total_gross"]*12),is_total=True)

    draw_row("Employer Contributions & Perquisites", "", None, None,       is_section=True); alt=False
    draw_row("PF employer contribution",        d["pf_label_ec"],          nf(d["pf_ec"]),       nf(d["pf_ec"]*12),      row_alt=alt); alt=not alt
    draw_row("ESIC employer contribution",
             "Employer rate 3.25%" if d["esic_eligible"] else "Employer rate 3.25%",
             nf(d["esic_emp_amt"]) if d["esic_eligible"] else "-",
             nf(d["esic_emp_amt"]*12) if d["esic_eligible"] else "-",      row_alt=alt); alt=not alt
    draw_row("Gratuity employer contribution",  "Gratuity rate 4.81%",    nf(d["gratuity"]),    nf(d["gratuity"]*12),   row_alt=alt); alt=not alt
    draw_row("Employee Health Insurance",       "Fully Taxable",           nf(d["health_ins"]),  nf(d["health_ins"]*12), row_alt=alt); alt=not alt
    draw_row("Total Employer Contributions &\nPerquisites (B)", "",        nf(d["total_ec"]),    nf(d["total_ec"]*12),   is_total=True)
    draw_row("Total CTC (Fixed) (A+B) (C)",    "",                        nf(d["total_ctc"]),   nf(d["total_ctc"]*12),  is_grand=True)

    draw_row("PLI/Bonus/Variable Pay (Subject to\nPerformance Review & paid anually)",
             "Performance Pay",                "-",                        "-",                  row_alt=False); alt=False
    draw_row("Total CTC (Including Variable) (D)", "",                    "-",                  nf(d["total_ctc"]*12),  is_grand=True)

    draw_row("Employee Contribution",           "", None, None,            is_section=True); alt=False
    draw_row("PF employee contribution",        d["pf_label_emp"],         nf(d["pf_emp"]),      nf(d["pf_emp"]*12),     row_alt=alt); alt=not alt
    draw_row("ESIC employee contribution",
             "Employee rate 0.75%" if d["esic_eligible"] else "Employee rate 0.75%",
             nf(d["esic_emp_amt2"]) if d["esic_eligible"] else "-",
             nf(d["esic_emp_amt2"]*12) if d["esic_eligible"] else "-",     row_alt=alt); alt=not alt
    draw_row("Professional Tax",                "NA",                      "-",                  "-",                    row_alt=alt); alt=not alt
    draw_row("Total Employee Contributions (E)","",                        nf(d["total_ded"]),   nf(d["total_ded"]*12),  is_total=True)
    draw_row("Net take Home (Before TDS) (A-E)","",                       nf(d["net_take_home"]),nf(d["net_take_home"]*12), is_net=True)

    # ── Outer border + vertical dividers ──────────────────────────────────
    c.setStrokeColorRGB(0,0,0); c.setLineWidth(0.8)
    c.rect(M, y, TW, table_top-y, fill=0, stroke=1)
    c.setLineWidth(0.35); c.setStrokeColorRGB(0.55,0.55,0.55)
    for cx in [CX[1], CX[2], CX[3]]:
        c.line(cx, y, cx, table_top)

    # ── Title bottom-right (exact original position) ──────────────────────
    y -= 10
    c.setFont(BI, 11); c.setFillColorRGB(0,0,0)
    c.drawRightString(W-M, y, "CTC Salary Annexure-1")

    # ── Notes ──────────────────────────────────────────────────────────────
    y -= 18
    c.setFont(BI, 8); c.setFillColorRGB(0,0,0)
    c.drawString(M, y, "Note:"); y -= 12
    c.setFont(B, 7.8); c.setFillColorRGB(0.2,0.2,0.2)
    pf_note = (f"PF calculated at 12% of Basic Salary (actual)."
               if d["pf_on_basic"]
               else "PF calculated at 12% of ₹15,000 (statutory cap) = ₹1,800 fixed.")
    notes = [
        f"1. ESIC & Statutory Bonus not eligible if monthly Gross Salary above Rs 21000/-",
        f"2. {pf_note}",
        "3. TDS will be calculated as per the applicable provisions of the Income Tax Act, 1961, and will be deducted from your monthly",
        "   salary accordingly. The deduction will be based on the tax regime chosen by you (Old or New) and the investment declarations",
        "   made during the financial year.",
        "4. The amount mentioned for health insurance in your CTC is approximate and is subject to change. The final premium will be",
        "   determined after submission of your family members' documents and required health declarations to the insurance provider.",
    ]
    for note in notes:
        c.drawString(M, y, note); y -= 11

    c.save(); buf.seek(0)
    return buf


# ── Trigger ───────────────────────────────────────────────────────────────────
if calc_btn and net_input:
    st.session_state.update({
        "d":        calc_ctc(int(net_input), pf_on_basic),
        "name":     emp_name,
        "desig":    emp_desig,
        "dept":     emp_dept,
        "eid":      emp_id,
        "company":  company_name,
        "pf_on_basic": pf_on_basic,
    })

# ── Display ───────────────────────────────────────────────────────────────────
if "d" in st.session_state:
    d       = st.session_state["d"]
    name    = st.session_state["name"]
    desig   = st.session_state["desig"]
    dept    = st.session_state.get("dept", "")
    eid     = st.session_state.get("eid", "")
    company = st.session_state.get("company", "")

    st.divider()
    if name:
        st.subheader(f"📄 {name}" + (f" — {desig}" if desig else ""))

    m1, m2, m3 = st.columns(3)
    m1.metric("Monthly CTC",   fmt(d["total_ctc"]))
    m2.metric("Annual CTC",    fmt(d["total_ctc"] * 12))
    m3.metric("Net Take-Home", fmt(d["net_take_home"]))

    if d["pf_on_basic"]:
        st.info(f"**PF basis:** 12% of Basic (₹{d['basic']:,}) → Employer PF: {fmt(d['pf_ec'])} / mo | Employee PF: {fmt(d['pf_emp'])} / mo")

    st.divider()

    cw = [4, 2.5, 1.8, 1.8]
    h  = st.columns(cw)
    h[0].markdown("**Component**"); h[1].markdown("**Type**")
    h[2].markdown("**Monthly**");   h[3].markdown("**Yearly**")
    st.markdown("---")

    table_row(cw, "Basic Salary",                    "Fully Taxable", d["basic"],      d["basic"]*12)
    table_row(cw, "House Rent Allowance",            "Fully Taxable", d["hra"],        d["hra"]*12)
    table_row(cw, "Statutory Bonus",                 "Fully Taxable", d["stat_bonus"], d["stat_bonus"]*12)
    table_row(cw, "Conveyance/ Transport Allowance", "Fully Taxable", d["conveyance"], d["conveyance"]*12)

    st.markdown(f"<div class='grand-total'>Total Gross Salary (A) &nbsp;|&nbsp; {fmt(d['total_gross'])} / mo &nbsp;|&nbsp; {fmt(d['total_gross']*12)} / yr</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Employer Contributions & Perquisites</div>", unsafe_allow_html=True)

    table_row(cw, "PF employer contribution",        d["pf_label_ec"],  d["pf_ec"],  d["pf_ec"]*12)
    table_row(cw, "ESIC employer contribution",
        "Employer rate 3.25%" if d["esic_eligible"] else "Not Eligible",
        d["esic_emp_amt"] if d["esic_eligible"] else None,
        d["esic_emp_amt"]*12 if d["esic_eligible"] else None)
    table_row(cw, "Gratuity employer contribution",  "Gratuity rate 4.81%", d["gratuity"],   d["gratuity"]*12)
    table_row(cw, "Employee Health Insurance",       "Fully Taxable",       d["health_ins"], d["health_ins"]*12)

    st.markdown(f"<div class='grand-total'>Total Employer Contributions & Perquisites (B) &nbsp;|&nbsp; {fmt(d['total_ec'])} / mo &nbsp;|&nbsp; {fmt(d['total_ec']*12)} / yr</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='grand-total'>Total CTC Fixed (A+B) (C) &nbsp;|&nbsp; {fmt(d['total_ctc'])} / mo &nbsp;|&nbsp; {fmt(d['total_ctc']*12)} / yr</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>PLI / Bonus / Variable Pay</div>", unsafe_allow_html=True)
    table_row(cw, "Performance Pay", "Subject to Performance Review", None, None)
    st.markdown(f"<div class='grand-total'>Total CTC Including Variable (D) &nbsp;|&nbsp; Annual: {fmt(d['total_ctc']*12)}</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>Employee Contributions</div>", unsafe_allow_html=True)
    table_row(cw, "PF employee contribution",  d["pf_label_emp"], d["pf_emp"], d["pf_emp"]*12)
    table_row(cw, "ESIC employee contribution",
        "Employee rate 0.75%" if d["esic_eligible"] else "Not Eligible",
        d["esic_emp_amt2"] if d["esic_eligible"] else None,
        d["esic_emp_amt2"]*12 if d["esic_eligible"] else None)
    table_row(cw, "Professional Tax", "NA", None, None)
    table_row(cw, "Total Employee Contributions (E)", "", d["total_ded"], d["total_ded"]*12, bold=True)

    st.markdown(f"<div class='net-total'>Net Take Home Before TDS (A−E) &nbsp;|&nbsp; {fmt(d['net_take_home'])} / mo &nbsp;|&nbsp; {fmt(d['net_take_home']*12)} / yr</div>", unsafe_allow_html=True)

    st.divider()
    esic_note = f"ESIC {'applicable' if d['esic_eligible'] else 'not applicable'} — gross ₹{d['gross']:,.0f} is {'below' if d['esic_eligible'] else 'above'} ₹21,000."
    st.info(f"**Notes:** {esic_note} | TDS per Income Tax Act 1961. | Health insurance amount approximate.")

    pdf_buf = build_pdf(d, name, desig, dept, eid, company)
    fname   = f"CTC_{(name or 'Employee').replace(' ', '_')}.pdf"
    st.download_button(
        label="⬇️ Download PDF",
        data=pdf_buf, file_name=fname,
        mime="application/pdf",
        use_container_width=True, type="primary"
    )
