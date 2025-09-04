import os, glob, smtplib, traceback
from dotenv import load_dotenv
from email.message import EmailMessage
from datetime import datetime

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO   = [e.strip() for e in os.getenv("EMAIL_TO","").split(",") if e.strip()]
SMTP_HOST  = os.getenv("SMTP_HOST","smtp.gmail.com")
SMTP_PORT  = int(os.getenv("SMTP_PORT","587"))
REPORTS_DIR = os.getenv("REPORTS_DIR","../data_analytics/reports")

def latest(mask): 
    files = glob.glob(mask); 
    return max(files, key=os.path.getmtime) if files else None

def build_and_send():
    print(f"FROM: {EMAIL_USER}")
    print(f"TO  : {EMAIL_TO}")
    print(f"SMTP: {SMTP_HOST}:{SMTP_PORT}")

    png = latest(os.path.join(REPORTS_DIR, "finance_report.png"))
    pdf = latest(os.path.join(REPORTS_DIR, "finance_report.pdf"))
    summary = latest(os.path.join(REPORTS_DIR, "finance_summary_*.pdf"))
    print("Attachments:", [x for x in [summary, pdf, png] if x])

    msg = EmailMessage()
    msg["Subject"] = f"Finance Report – {datetime.now():%Y-%m-%d}"
    msg["From"] = EMAIL_USER
    msg["To"] = ", ".join(EMAIL_TO)
    msg.set_content("Կցված են վերջին հաշվետվությունների PDF/PNG ֆայլերը։")

    for f in [summary, pdf, png]:
        if not f: 
            continue
        with open(f, "rb") as fp:
            data = fp.read()
        maintype, subtype = ("application","pdf") if f.endswith(".pdf") else ("image","png")
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=os.path.basename(f))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.set_debuglevel(1)  # 🔍 SMTP debug to console
            s.starttls()
            s.login(EMAIL_USER, EMAIL_PASS)
            s.send_message(msg)
        print("✅ SENT")
    except Exception as e:
        print("❌ SEND FAILED:", e)
        traceback.print_exc()

if __name__ == "__main__":
    os.makedirs(REPORTS_DIR, exist_ok=True)
    build_and_send()

