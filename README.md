# 💼 CTC Structure Generator

A Streamlit web app to generate professional CTC (Cost to Company) salary structures from a net take-home salary input. Produces a downloadable PDF matching the standard CTC Salary Annexure format.

## 🚀 Live App

> Deploy on [Streamlit Cloud](https://streamlit.io/cloud) — see deployment steps below.

---

## 📐 Salary Calculation Logic

| Component | Formula |
|---|---|
| **Basic Salary** | 50% of Total CTC |
| **HRA** | 50% of Basic |
| **Statutory Bonus** | 15% of Basic (always applicable) |
| **Conveyance** | Gross − Basic − HRA − Statutory Bonus |
| **Gratuity (Employer)** | 4.81% of Basic |
| **PF (Employer & Employee)** | 12% of ₹15,000 = ₹1,800 each |
| **ESIC** | Applicable only when Gross < ₹21,000 (3.25% employer / 0.75% employee) |
| **Health Insurance** | ₹500/month fixed |

---

## 🖥️ Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/ctc-structure-generator.git
cd ctc-structure-generator

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

App will open at `http://localhost:8501`

---

## ☁️ Deploy on Streamlit Cloud

1. Push this repo to GitHub (public or private)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **"New app"**
4. Select your repository, branch (`main`), and set **Main file path** to `app.py`
5. Click **Deploy** — your app will be live in ~2 minutes!

---

## 📄 Features

- Enter net monthly salary → full CTC breakdown auto-calculated
- ESIC eligibility auto-detected based on gross salary
- Download a formatted PDF matching the standard CTC Annexure format
- Employee name & designation on the PDF
- Color-coded totals (blue for CTC, green for net take-home)

---

## 📁 Project Structure

```
ctc-structure-generator/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## 📝 License

MIT License — free to use and modify.
