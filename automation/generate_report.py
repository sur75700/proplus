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

import os
from datetime import datetime, date

GOAL_AMOUNT = int(os.getenv("GOAL_AMOUNT", "300000"))
GOAL_DATE   = os.getenv("GOAL_DATE", "2025-09-26")  # YYYY-MM-DD



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

def calc_goal_block(data, goal_amount, goal_date_str):
    from datetime import datetime, date
    last = data[-1] if data else {}
    cur = int(last.get("savings", 0) or 0)
    goal_dt = date.fromisoformat(goal_date_str)
    today = date.today()
    days_left = max((goal_dt - today).days, 0)
    remaining = max(goal_amount - cur, 0)
    pct = 0 if goal_amount <= 0 else min(100.0, round(cur * 100.0 / goal_amount, 1))
    need_per_day = round(remaining / max(days_left, 1), 2)
    return {
        "goal_amount": goal_amount,
        "goal_date": goal_dt.isoformat(),
        "current_savings": cur,
        "progress_pct": pct,
        "remaining": remaining,
        "days_left": days_left,
        "need_per_day": need_per_day,
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

import os
from datetime import datetime, date
GOAL_AMOUNT = int(os.getenv("GOAL_AMOUNT", "300000"))
GOAL_DATE   = os.getenv("GOAL_DATE", "2025-09-26")

# ---------- Main ----------
def main():
    # 1) Տվյալներ քաշել DB-ից (քո գոյություն ունեցող ֆունկցիան)
    data = fetch_data()
    if not data:
        print("ℹ️ Տվյալներ չկան՝ report չի ստեղծվի.")
        return

    # 2) Ճանապարհներ
    chart_path = REPORTS_DIR / "finance_report.png"
    pdf_path   = REPORTS_DIR / "finance_report.pdf"

    # 3) Գրաֆիկ
    create_chart(data, chart_path)

    # 4) Ամփոփում + Նպատակի բլոկ
    summary    = calc_summary(data)
    goal_block = calc_goal_block(data, GOAL_AMOUNT, GOAL_DATE)

    # 5) PDF
    build_pdf(summary, chart_path, pdf_path, goal_block)

    print(f"✅ PNG: {chart_path}")
    print(f"✅ PDF: {pdf_path}")

def calc_goal_block(data, goal_amount, goal_date_str):
    """
    Հաշվում ա նպատակի progress-ը (օր.՝ 300000 դրամ մինչև 2025-09-26):
    Վերադարձնում ա dict, որ հետո PDF-ում ցույց տանք։
    """
    from datetime import datetime

    # Վերջին savings
    last = data[-1] if data else {}
    current_savings = last.get("savings", 0)

    # Նպատակի վերջնաժամկետ
    goal_date = datetime.strptime(goal_date_str, "%Y-%m-%d").date()
    days_left = (goal_date - datetime.now().date()).days

    # Progress %
    progress_pct = min(100, round(current_savings * 100 / goal_amount, 2)) if goal_amount > 0 else 0

    return {
        "goal_amount": goal_amount,
        "goal_date": goal_date_str,
        "current_savings": current_savings,
        "progress_pct": progress_pct,
        "days_left": days_left
    }



from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

def progress_bar(flowables, pct: float, width_mm=160, height_mm=8):
    # այս flowable-ը կստեղծենք պատկերից՝ ReportLab-ի canvas-ով
    from reportlab.lib.colors import HexColor
    tmp_png = REPORTS_DIR / "goal_bar.png"

    bar_w = width_mm * mm
    bar_h = height_mm * mm
    fill_w = bar_w * (pct / 100.0)

    c = canvas.Canvas(str(tmp_png), pagesize=(bar_w, bar_h))
    # ֆոն
    c.setFillColor(HexColor("#e6e6e6"))
    c.rect(0, 0, bar_w, bar_h, fill=1, stroke=0)
    # լցված հատված
    c.setFillColor(HexColor("#4caf50"))  # կանաչ
    c.rect(0, 0, fill_w, bar_h, fill=1, stroke=0)
    c.save()

    from reportlab.platypus import Image, Spacer
    flowables += [Image(str(tmp_png), width=bar_w, height=bar_h), Spacer(1, 6)]


def build_pdf(summary, chart_path: Path, pdf_path: Path, goal_block: dict):
    styles = getSampleStyleSheet()
    story = []

    # Վերնագիր + ամսաթիվ
    title = Paragraph("📊 Ֆինանսական Հաշվետվություն", styles["Title"])
    datep = Paragraph(f"Ստեղծված է՝ {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"])
    story += [title, Spacer(1, 8), datep, Spacer(1, 16)]

    # Գրաֆիկ
    story += [Image(str(chart_path), width=500, height=260), Spacer(1, 18)]

    # Ամփոփ աղյուսակ (քո արդեն եղած table_data-ը)
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
    story += [t, Spacer(1, 16)]

    # === 🟢 GOAL TRACKER ===
    story += [Paragraph("🎯 Նպատակի Թրեքեր (մինչև {:%Y-%m-%d})".format(
        datetime.strptime(GOAL_DATE, "%Y-%m-%d")), styles["Heading2"]),
        Spacer(1, 6)
    ]

    goal_tbl = Table([
        ["Ներկա գումար (savings)", f"{goal_block['current']:,} դրամ".replace(",", " ")],
        ["Թիրախ",                  f"{goal_block['goal']:,} դրամ".replace(",", " ")],
        ["Մնաց",                   f"{goal_block['remaining']:,} դրամ".replace(",", " ")],
        ["Մնացած օրեր",            f"{goal_block['days_left']} օր"],
        ["Օրական անհրաժեշտ",       f"{goal_block['daily_need']:,} դրամ/օր".replace(",", " ")],
        ["Առաջընթաց",              f"{goal_block['progress_pct']}%"],
    ], colWidths=[220, 220], hAlign="LEFT")
    goal_tbl.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story += [goal_tbl, Spacer(1, 8)]

    # progress bar
    progress_bar(story, goal_block["progress_pct"])

    footer = Paragraph("Ստեղծվել է ProPlus համակարգի միջոցով", styles["Italic"])
    story += [Spacer(1, 10), footer]

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
    doc.build(story)
