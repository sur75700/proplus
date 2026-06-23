#!/usr/bin/env bash
set -e
API=${API:-http://127.0.0.1:8100}

echo "[1] health"; curl -s ${API}/healthz; echo
echo "[2] register"; curl -s -X POST ${API}/auth/register -H "Content-Type: application/json" -d '{"email":"a@a.com","password":"Password12345"}'; echo
echo "[3] login"; LOGIN=$(curl -s -X POST ${API}/auth/login -H "Content-Type: application/json" -d '{"email":"a@a.com","password":"Password12345"}'); echo $LOGIN
AT=$(echo $LOGIN | python - <<'PY'
import sys,json; print(json.load(sys.stdin)["access_token"])
PY
)
RT=$(echo $LOGIN | python - <<'PY'
import sys,json; print(json.load(sys.stdin)["refresh_token"])
PY
)
echo "[4] me"; curl -s ${API}/auth/me -H "Authorization: Bearer ${AT}"; echo
echo "[5] refresh"; curl -s -X POST ${API}/auth/refresh -H "Content-Type: application/json" -d "{\"refresh_token\":\"${RT}\"}"; echo
