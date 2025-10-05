#!/usr/bin/env bash
set -euo pipefail

BASE="http://127.0.0.1:8000"
EMAIL="b@b.com"
PASS="123456"

TOKEN=$(
  curl -s -X POST "$BASE/auth/login" -H 'Content-Type: application/json' \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" | awk -F'"' '/access_token/{print $4}'
)
echo "TOKEN=${TOKEN:0:20}..."

CREATE_RES=$(curl -s -X POST "$BASE/projects" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Smoke Test","description":"demo"}')
echo "CREATE=$CREATE_RES"

PID=$(printf '%s' "$CREATE_RES" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p')
echo "PID=$PID"

echo "LIST=$(curl -s "$BASE/projects" -H "Authorization: Bearer $TOKEN")"
echo "UPDATE=$(curl -s -X PUT "$BASE/projects/$PID" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Smoke Updated","description":"changed"}')"
echo "DELETE=$(curl -s -X DELETE "$BASE/projects/$PID" -H "Authorization: Bearer $TOKEN")"
