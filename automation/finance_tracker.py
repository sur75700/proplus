#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Finance Tracker (Pro++)
- MongoDB insert/read
- Safe query (only valid docs)
- CLI: add, plot
"""

import os
import sys
import argparse
import datetime as dt
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient, errors
import matplotlib.pyplot as plt


# ---------- Env & Paths ----------
ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

MONGO_URI  = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB   = os.getenv("MONGO_DB", "proplus")
MONGO_COL  = os.getenv("MONGO_COLLECTION", "finance")

REPORTS_DIR = Path(os.getenv("REPORTS_DIR", ROOT.parent / "data_analytics" / "reports"))
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------- DB helpers ----------
def get_collection():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # ping
        client.admin.command("ping")
        return client[MONGO_DB][MONGO_COL]
    except errors.PyMongoError as e:
        print(f"❌ MongoDB connection error: {e}")
        sys.exit(2)


def fetch_valid_docs(col):
    """Return only documents that surely have income/debt/savings, sorted by ts."""
    query = {
        "income":  {"$exists": True},
        "debt":    {"$exists": True},
        "savings": {"$exists": True},
    }
    return list(col.find(query).sort("ts", 1))


# ---------- Commands ----------
def cmd_add(args):
    col = get_collection()
    now = dt.datetime.now()

    record = {
        "income":  int(args.income),
        "debt":    int(args.debt),
        "savings": int(args.savings),
        "ts":      now,
    }
    res = col.insert_one(record)
    print(f"✅ Data saved to MongoDB: {record} | _id={res.inserted_id}")


def cmd_plot(args):
    col = get_collection()
    data = fetch_valid_docs(col)
    if not data:
        print("ℹ️ No data to plot (collection is empty or filtered out).")
        return

    x = [d.get("ts") or dt.datetime.now() for d in data]
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

    out_png = REPORTS_DIR / "finance_report.png"
    plt.savefig(out_png)
    plt.show(block=False)  # չկասեցնի տերմինալը
    print(f"✅ Chart saved: {out_png}")


# ---------- CLI ----------
def build_parser():
    p = argparse.ArgumentParser(description="Finance Tracker Pro++")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="Add a new record")
    p_add.add_argument("--income",  required=True, type=int)
    p_add.add_argument("--debt",    required=True, type=int)
    p_add.add_argument("--savings", required=True, type=int)
    p_add.set_defaults(func=cmd_add)

    p_plot = sub.add_parser("plot", help="Plot chart from MongoDB")
    p_plot.set_defaults(func=cmd_plot)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
