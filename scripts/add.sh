#!/usr/bin/env bash
# Usage: ./scripts/add.sh 200000 800000 150000
set -euo pipefail

income="${1:-}"; debt="${2:-}"; savings="${3:-}"
if [[ -z "$income" || -z "$debt" || -z "$savings" ]]; then
  echo "Usage: $0 <income> <debt> <savings>"
  exit 1
fi

docker exec -it proplus_app bash -lc \
  "python finance_tracker.py add --income \"$income\" --debt \"$debt\" --savings \"$savings\""
