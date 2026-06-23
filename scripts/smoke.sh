#!/usr/bin/env bash
set -euo pipefail

API="${API:-http://127.0.0.1:8100}"
EMAIL="${EMAIL:-gazan_$(date +%s)@example.com}"
PASS="${PASS:-StrongPass12345}"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

REG_JSON="$TMP_DIR/register.json"
LOGIN_JSON="$TMP_DIR/login.json"
REFRESH_JSON="$TMP_DIR/refresh.json"

echo "👑 PROPLUS SMOKE TEST"
echo "API:   $API"
echo "EMAIL: $EMAIL"
echo

extract_token() {
  python3 - "$1" "$2" <<'PY'
import json
import sys

path, key = sys.argv[1], sys.argv[2]
with open(path) as f:
    data = json.load(f)

print(data.get(key, ""))
PY
}

redacted_token_summary() {
  python3 - "$1" <<'PY'
import json
import sys

with open(sys.argv[1]) as f:
    data = json.load(f)

print({
    "access_token": bool(data.get("access_token")),
    "refresh_token": bool(data.get("refresh_token")),
    "token_type": data.get("token_type"),
})
PY
}

echo "👑 [1] healthz"
curl -fsS "$API/healthz"
echo
echo

echo "👑 [2] readyz"
curl -fsS "$API/readyz"
echo
echo

echo "👑 [3] register"
curl -fsS -X POST "$API/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" \
  | tee "$REG_JSON"
echo
echo

echo "👑 [4] login"
curl -fsS -X POST "$API/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" \
  > "$LOGIN_JSON"
redacted_token_summary "$LOGIN_JSON"
echo
echo

ACCESS_TOKEN="$(extract_token "$LOGIN_JSON" access_token)"
REFRESH_TOKEN="$(extract_token "$LOGIN_JSON" refresh_token)"

if [ -z "$ACCESS_TOKEN" ] || [ -z "$REFRESH_TOKEN" ]; then
  echo "❌ Missing access or refresh token"
  exit 1
fi

echo "✅ Tokens received"
echo

echo "👑 [5] me"
curl -fsS "$API/auth/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
echo
echo

echo "👑 [6] refresh"
curl -fsS -X POST "$API/auth/refresh" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}" \
  > "$REFRESH_JSON"
redacted_token_summary "$REFRESH_JSON"
echo
echo

NEW_REFRESH_TOKEN="$(extract_token "$REFRESH_JSON" refresh_token)"

if [ -z "$NEW_REFRESH_TOKEN" ]; then
  echo "❌ Missing rotated refresh token"
  exit 1
fi

echo "👑 [7] old refresh token reuse should be 401"
REUSE_CODE="$(curl -s -o "$TMP_DIR/reuse.json" -w "%{http_code}" -X POST "$API/auth/refresh" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}")"

echo "refresh_reuse_http_status=$REUSE_CODE"
if [ "$REUSE_CODE" != "401" ]; then
  echo "❌ Expected 401 for refresh token reuse"
  cat "$TMP_DIR/reuse.json"
  echo
  exit 1
fi

echo
echo "👑 [8] logout"
curl -fsS -X POST "$API/auth/logout" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$NEW_REFRESH_TOKEN\"}" \
  -o /dev/null \
  -w "logout_http_status=%{http_code}\n"

echo
echo "👑 [9] invalid token returns 401"
HTTP_CODE="$(curl -s -o "$TMP_DIR/invalid_token.json" -w "%{http_code}" "$API/auth/me" \
  -H "Authorization: Bearer bad.token.value")"

echo "invalid_token_http_status=$HTTP_CODE"

if [ "$HTTP_CODE" != "401" ]; then
  echo "❌ Expected 401 for invalid token"
  cat "$TMP_DIR/invalid_token.json"
  echo
  exit 1
fi

echo
echo "✅ PROPLUS SMOKE TEST PASSED"
