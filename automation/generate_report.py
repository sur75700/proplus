#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate Finance Report (Pro++)
- Reads from MongoDB (safe query)
- Matplotlib chart -> PNG
- ReportLab PDF with summary
"""

import os
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from pymongo import MongoClient, errors
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

MONGO_URI  = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB   = os.getenv("MONGO_DB", "proplus")
MONGO_COL  = os.getenv("MONGO_COLLECTION", "finance")

REPORTS_DIR = Path(os.getenv("REPORTS_DIR", ROOT.parent / "data_analytics" / "reports"))
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------- DB ----------
def get_collection():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    return client[MONGO_DB][MONGO_COL]


def fetch_data():
    col = get_collection()
    query = {"income":{"$exists":True}, "debt":{"$exists":True}, "savings":{"$exists":True}}
    return list(col.find(query).sort("ts", 1))


# ---------- Chart ----------
def create_chart(data, chart_path: Path):
    if not data:
        raise RuntimeError("No data to chart")

    x = [d.get("ts") for d in data]
    income  = [d.get("income", 0)  for d in data]
    debt    = [d.get("debt", 0)    for d in data]
    savings = [d.get("savings", 0) for d in data]

    plt.figure(figsize=(8, 5))
    plt.plot(x, income, marker="o", label="Եկամուտ (Income)")
    plt.plot(x, debt, marker="o", label="Պարտք (Debt)")
    plt.plot(x, savings, marker="o", label="Խնայողություն (Savings)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close()


# ---------- Summary ----------
def calc_summary(data):
    first, last = data[0], data[-1]

    def pct(from_, to_):
        try:
            if from_ == 0:
                return 0.0
            return (to_ - from_) * 100.0 / from_
        except Exception:
            return 0.0

    inc_g = pct(first.get("income", 0), last.get("income", 0))
    deb_r = pct(first.get("debt", 0),   last.get("debt", 0)) * -1  # debt reduction positive
    sav_g = pct(first.get("savings", 0), last.get("savings", 0))

    return {
        "latest_income":  last.get("income", 0),
        "latest_debt":    last.get("debt", 0),
        "latest_savings": last.get("savings", 0),
        "income_growth_pct":  round(inc_g, 1),
        "debt_reduction_pct": round(deb_r, 1),
        "savings_growth_pct": round(sav_g, 1),
    }


# ---------- PDF ----------
def build_pdf(summary, chart_path: Path, pdf_path: Path):
    styles = getSampleStyleSheet()
    story = []

    title = Paragraph("📊 Ֆինանսական Հաշվետվություն", styles["Title"])
    datep = Paragraph(f"Ստեղծված է՝ {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"])

    story += [title, Spacer(1, 8), datep, Spacer(1, 16)]
    story += [Image(str(chart_path), width=500, height=260), Spacer(1, 18)]

    table_data = [
        ["Ցուցիչ", "Արժեք"],
        ["Վերջին Եկամուտ",       f"{summary['latest_income']:,} դրամ".replace(",", " ")],
        ["Վերջին Պարտք",         f"{summary['latest_debt']:,} դրամ".replace(",", " ")],
        ["Վերջին Խնայողություն",  f"{summary['latest_savings']:,} դրամ".replace(",", " ")],
        ["Եկամուտի աճ %",         f"{summary['income_growth_pct']}%"],
        ["Պարտքի նվազում %",      f"{summary['debt_reduction_pct']}%"],
        ["Խնայողության աճ %",     f"{summary['savings_growth_pct']}%"],
    ]

    t = Table(table_data, hAlign="LEFT", colWidths=[220, 220])
    t.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0,0), (-1,0), 8),
    ]))
    story += [t, Spacer(1, 12)]

    footer = Paragraph("Ստեղծվել է ProPlus համակարգի միջոցով", styles["Italic"])
    story += [footer]

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
    doc.build(story)


# ---------- Main ----------
def main():
    try:
        data = fetch_data()
    except errors.PyMongoError as e:
        print(f"❌ MongoDB error: {e}")
        return

    if not data:
        print("ℹ️ Տվյալներ չկան (կամ ֆիլտրով մերժվել են). Ավելացրու գրառումներ `finance_tracker.py add ...`")
        return

    chart_path = REPORTS_DIR / "finance_report.png"
    pdf_path   = REPORTS_DIR / "finance_report.pdf"

    create_chart(data, chart_path)
    summary = calc_summary(data)
    build_pdf(summary, chart_path, pdf_path)

    print(f"✅ PNG: {chart_path}")
    print(f"✅ PDF: {pdf_path}")


if __name__ == "__main__":
    main()
