# automation/streamlit_app.py
from __future__ import annotations

import os
from datetime import datetime, timezone

import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient
from bson.objectid import ObjectId
import streamlit as st

# ---------- Settings ----------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
MONGO_DB = os.getenv("MONGO_DB", "proplus")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "finance")

SAVINGS_GOAL = float(os.getenv("SAVINGS_GOAL", "300000"))  # change via env if needed


# ---------- DB ----------
@st.cache_resource
def get_collection():
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    return db[MONGO_COLLECTION]


collection = get_collection()


# ---------- Helpers ----------
def _to_df(docs: list[dict]) -> pd.DataFrame:
    if not docs:
        return pd.DataFrame()
    df = pd.DataFrame(docs).copy()

    # Normalize timestamp column
    if "ts" in df.columns:
        # handle both str and datetime
        df["ts"] = pd.to_datetime(df["ts"], errors="coerce", utc=True).dt.tz_convert(
            None
        )
    else:
        df["ts"] = pd.NaT

    # Ensure numeric columns exist
    for col in ["income", "debt", "savings"]:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # Sort by time
    df = df.sort_values("ts").reset_index(drop=True)
    return df


def insert_record(income: float, debt: float, savings: float) -> ObjectId:
    doc = {
        "income": float(income),
        "debt": float(debt),
        "savings": float(savings),
        "ts": datetime.now(timezone.utc),
    }
    res = collection.insert_one(doc)
    return res.inserted_id


# ---------- UI ----------
st.set_page_config(
    page_title="💰 ProPlus Finance Dashboard", page_icon="💰", layout="wide"
)
st.title("💰 ProPlus Finance Dashboard")

with st.sidebar:
    st.header("➕ Add a record")
    with st.form("add_form", clear_on_submit=True):
        income_in = st.number_input("Income", min_value=0.0, step=1000.0, value=0.0)
        debt_in = st.number_input("Debt", min_value=0.0, step=1000.0, value=0.0)
        savings_in = st.number_input("Savings", min_value=0.0, step=1000.0, value=0.0)
        submitted = st.form_submit_button("Save to MongoDB")
        if submitted:
            _id = insert_record(income_in, debt_in, savings_in)
            st.success(f"Saved ✅ (id={_id})")

    st.divider()
    st.caption("⚙️ Settings")
    goal_val = st.number_input(
        "Savings goal (override runtime)",
        min_value=0.0,
        step=5000.0,
        value=SAVINGS_GOAL,
    )

# Load data
docs = list(collection.find({}))
df = _to_df(docs)

# Empty-state
if df.empty:
    st.warning(
        "⛔ Database is empty. Add a record from the left panel or run `make add ...`."
    )
    st.stop()

# ---------- KPIs ----------
latest = df.iloc[-1]
col1, col2, col3, col4 = st.columns(4)
col1.metric("Income (latest)", f"{latest['income']:,.0f}")
col2.metric("Debt (latest)", f"{latest['debt']:,.0f}")
col3.metric("Savings (latest)", f"{latest['savings']:,.0f}")

total_savings = float(df["savings"].sum())
progress = min(total_savings / max(goal_val, 1.0), 1.0)
col4.metric("Savings total", f"{total_savings:,.0f}")

st.subheader("🎯 Goal progress")
st.progress(progress, text=f"{total_savings:,.0f} / {goal_val:,.0f}")

# ---------- Chart ----------
st.subheader("📈 Time series")
fig, ax = plt.subplots()
# Only plot columns that exist & have variation
plot_cols = [c for c in ["income", "debt", "savings"] if c in df.columns]
if df["ts"].notna().any():
    ax.plot(df["ts"], df[plot_cols])
    ax.set_xlabel("Timestamp")
else:
    ax.plot(range(len(df)), df[plot_cols])
    ax.set_xlabel("Index")

ax.set_ylabel("Amount")
ax.grid(True, alpha=0.3)
ax.legend(plot_cols)
st.pyplot(fig, clear_figure=True)

# ---------- Table ----------
st.subheader("🧾 Last 20 records")
st.dataframe(df.tail(20), use_container_width=True)

# ---------- Download ----------
st.subheader("⬇️ Export")
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download CSV", data=csv, file_name="finance_data.csv", mime="text/csv"
)
