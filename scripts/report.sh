#!/usr/bin/env bash
# Generates chart (PNG) + PDF report and sends email (based on your .env)
set -euo pipefail

docker exec -it proplus_app bash -lc "python finance_tracker.py plot"
docker exec -it proplus_app bash -lc "python generate_report.py"
