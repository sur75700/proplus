#!/usr/bin/env bash
set -e

docker exec -i proplus_app python - <<'PY'
import os, pandas as pd
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI","mongodb://localhost:27017/")
DB        = os.getenv("MONGO_DB","proplus")
COL       = os.getenv("MONGO_COLLECTION","finance")
OUT       = "/app/data_analytics/reports/finance_data.csv"

col = MongoClient(MONGO_URI)[DB][COL]
docs = list(col.find({
  "income":{"$exists":True},
  "debt":{"$exists":True},
  "savings":{"$exists":True}
}).sort("ts",1))

for d in docs: d.pop("_id", None)
if not docs:
    print("No data to export"); raise SystemExit(0)

pd.DataFrame(docs).to_csv(OUT, index=False)
print(f"CSV saved -> {OUT}")
PY

