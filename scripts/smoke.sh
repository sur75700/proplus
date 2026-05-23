#!/usr/bin/env bash
set -euo pipefail

API="${API_BASE_URL:-http://localhost:8000}"
EMAIL="${EMAIL:-admin@proplus.com}"
PASS="${PASS:-Admin123!}"

jget(){ python - "$@" <<'PY' ;}
import sys, json, os
print(json.load(sys.stdin).get(os.environ["KEY"], ""))
PY
}

echo "→ Login as ${EMAIL}"
TOKENS="$(curl -s -X POST "$API/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}")"

KEY=access_token  AT="$(printf '%s' "$TOKENS" | jget)"
KEY=refresh_token RT="$(printf '%s' "$TOKENS" | jget)"

echo "  access: ${AT:0:24}... (dots=$(printf '%s' "$AT" | tr -cd '.' | wc -c))"
echo "  refresh: ${RT:0:24}..."

echo "→ /auth/me"
curl -s "$API/auth/me" -H "Authorization: Bearer $AT" | python -m json.tool

echo "→ /auth/refresh"
NEW="$(curl -s -X POST "$API/auth/refresh" \
  -H 'Content-Type: application/json' \
  -d "{\"refresh_token\":\"$RT\"}")"
KEY=access_token  AT2="$(printf '%s' "$NEW" | jget)"
echo "  new access: ${AT2:0:24}..."

echo "→ /admin/users (first page)"
curl -s "$API/admin/users?page=1&limit=10" -H "Authorization: Bearer $AT2" | python -m json.tool
