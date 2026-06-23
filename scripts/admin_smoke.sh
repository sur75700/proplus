#!/usr/bin/env bash
set -euo pipefail

API="${API:-http://127.0.0.1:8100}"
USER_EMAIL="${USER_EMAIL:-normal_$(date +%s)@example.com}"
USER_PASS="${USER_PASS:-StrongPass12345}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin_$(date +%s)@example.com}"
ADMIN_PASS="${ADMIN_PASS:-StrongAdminPass12345}"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

USER_LOGIN_JSON="$TMP_DIR/user_login.json"
ADMIN_LOGIN_JSON="$TMP_DIR/admin_login.json"

echo "👑 PROPLUS ADMIN SMOKE TEST"
echo "API:         $API"
echo "USER_EMAIL:  $USER_EMAIL"
echo "ADMIN_EMAIL: $ADMIN_EMAIL"
echo

http_code() {
  local output="$1"
  shift
  curl -s -o "$output" -w "%{http_code}" "$@"
}

expect_code() {
  local name="$1"
  local got="$2"
  local expected="$3"
  local body="$4"

  echo "$name -> HTTP $got"

  if [ "$got" != "$expected" ]; then
    echo "❌ Expected $expected but got $got"
    echo "Body:"
    cat "$body"
    echo
    exit 1
  fi
}

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

echo "👑 [1] readiness"
curl -fsS "$API/readyz"
echo
echo

echo "👑 [2] admin without token should be 401"
BODY="$TMP_DIR/no_token.json"
CODE="$(http_code "$BODY" "$API/admin/users")"
expect_code "no_token" "$CODE" "401" "$BODY"

echo
echo "👑 [3] admin with bad token should be 401"
BODY="$TMP_DIR/bad_token.json"
CODE="$(http_code "$BODY" "$API/admin/users" -H "Authorization: Bearer bad.token.value")"
expect_code "bad_token" "$CODE" "401" "$BODY"

echo
echo "👑 [4] create normal user"
curl -fsS -X POST "$API/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$USER_EMAIL\",\"password\":\"$USER_PASS\"}" >/dev/null

curl -fsS -X POST "$API/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$USER_EMAIL\",\"password\":\"$USER_PASS\"}" \
  > "$USER_LOGIN_JSON"

USER_AT="$(extract_token "$USER_LOGIN_JSON" access_token)"

if [ -z "$USER_AT" ]; then
  echo "❌ normal user access token missing"
  exit 1
fi

echo "✅ normal user token received"

echo
echo "👑 [5] normal user admin access should be 403"
BODY="$TMP_DIR/user_admin.json"
CODE="$(http_code "$BODY" "$API/admin/users" -H "Authorization: Bearer $USER_AT")"
expect_code "normal_user_admin" "$CODE" "403" "$BODY"

echo
echo "👑 [6] create + promote admin user through local Mongo helper"
ADMIN_EMAIL="$ADMIN_EMAIL" ADMIN_PASS="$ADMIN_PASS" python3 - <<'PY'
import asyncio
import os

from app.db import users
from app.models import create_user

email = os.environ["ADMIN_EMAIL"]
password = os.environ["ADMIN_PASS"]


async def main():
    await create_user(email, password)
    await users.update_one(
        {"email": email},
        {"$set": {"role": "admin", "email_verified": True}},
        upsert=False,
    )
    print("admin_ready=true")


asyncio.run(main())
PY

echo
echo "👑 [7] login admin"
curl -fsS -X POST "$API/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASS\"}" \
  > "$ADMIN_LOGIN_JSON"

ADMIN_AT="$(extract_token "$ADMIN_LOGIN_JSON" access_token)"

if [ -z "$ADMIN_AT" ]; then
  echo "❌ admin access token missing"
  exit 1
fi

echo "✅ admin token received"

echo
echo "👑 [8] admin users should be 200"
BODY="$TMP_DIR/admin_users.json"
CODE="$(http_code "$BODY" "$API/admin/users" -H "Authorization: Bearer $ADMIN_AT")"
expect_code "admin_users" "$CODE" "200" "$BODY"

echo
echo "👑 [9] admin bad ObjectId should be 400"
BODY="$TMP_DIR/bad_oid.json"
CODE="$(http_code "$BODY" "$API/admin/users/not-a-valid-objectid" -H "Authorization: Bearer $ADMIN_AT")"
expect_code "bad_object_id" "$CODE" "400" "$BODY"

echo
echo "✅ PROPLUS ADMIN SMOKE TEST PASSED"
