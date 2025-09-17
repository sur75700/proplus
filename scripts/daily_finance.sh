#!/usr/bin/env bash
set -euo pipefail
cd ~/Projects/ProPlus

# Թվերը կարող ես փոխանցել կանչելիս.
# օրինակ: daily_finance.sh 12000 3000 2000
INCOME="${1:-0}"
DEBT="${2:-0}"
SAVINGS="${3:-0}"

# containers must be up
docker compose up -d

# 1) Add entry
make add income="$INCOME" debt="$DEBT" savings="$SAVINGS"

# 2) Build report (PNG/PDF)
make report

# 3) Send email
make email
