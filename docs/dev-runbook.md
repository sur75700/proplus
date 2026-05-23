# ProPlus Developer Runbook

## Current State

ProPlus backend is now a FastAPI + MongoDB + Redis platform with Docker boot, health checks, JWT auth, refresh rotation, refresh reuse detection, admin RBAC, Mongo indexes, auth smoke tests, and admin smoke tests.

## Current Branch

phase-1d-api-security-polish

## Important Checkpoints

e02800c feat: detect refresh token reuse and revoke active chain
b396cb4 feat: harden admin auth dependency and add admin smoke test
02f84e0 feat: add Mongo indexes and redact smoke test tokens
20ba163 chore: harden docker backend boot and healthchecks
f99d4b0 feat: add readiness checks and backend smoke hardening
78f45aa fix: stabilize backend auth boot and local email dev mode
fb32056 chore: separate product code from arsenal secrets and quarantine artifacts

## Start Docker

cd ~/Projects/ProPlus/data_analytics
docker compose up -d
docker compose ps

Expected: api, mongo, redis should be healthy.

## Stop Docker

docker compose down

## Health Checks

curl -fsS http://127.0.0.1:8000/healthz; echo
curl -fsS http://127.0.0.1:8000/readyz; echo

Expected:
{"ok":true,"service":"proplus-api"}
{"ready":true,"checks":{"mongo":true,"redis":true}}

## Auth Smoke

API="http://127.0.0.1:8000" ./scripts/smoke.sh

Expected:
PROPLUS SMOKE TEST PASSED

## Admin Smoke

export MONGO_URL="mongodb://localhost:27017/proplus"
export REDIS_URL="redis://localhost:6379/0"
export PRIVATE_KEY_PATH="secrets/jwt_private.pem"
export PUBLIC_KEY_PATH="secrets/jwt_public.pem"
export EMAIL_DEV_MODE="true"

API="http://127.0.0.1:8000" ./scripts/admin_smoke.sh

Expected:
PROPLUS ADMIN SMOKE TEST PASSED

## Safety Rules

Never commit:
.env
secrets/
*.pem
*.key
*.asc
*.gpg
payloads
quarantine artifacts
local arsenal tools

Arsenal path:
~/Tools/ProPlus-Arsenal

Local JWT keys:
secrets/jwt_private.pem
secrets/jwt_public.pem

## Completed Phases

PHASE 1A - Backend auth boot stabilized
PHASE 1B - Readiness and smoke hardening
PHASE 1C - Docker backend boot hardening
PHASE 1D Part 1 - Mongo indexes and smoke token redaction
PHASE 1D Part 2 - Admin auth hardening and admin smoke
PHASE 1D Part 3 - Refresh token reuse detection

## Next Recommended Phase

PHASE 1E - Developer Experience and API Documentation Polish
