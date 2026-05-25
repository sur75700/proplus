# ProPlus Developer Runbook

## Current State

ProPlus backend is a FastAPI + MongoDB + Redis platform with Docker boot, health checks, JWT auth, refresh rotation, refresh reuse detection, admin RBAC, Mongo indexes, structured error responses, request ID tracing, auth/admin smoke tests, pytest coverage, ruff quality gates, and GitHub Actions CI.

## Current Branch

main

## Current Phase

PHASE 1I — Backend Production Hardening

## Current Stable Checkpoint

Expected current state:

- main branch
- GitHub Actions green
- 37 pytest tests passing
- ruff passing
- OpenAPI summary passing
- auth smoke passing
- admin smoke passing
- clean product repository
- local Ghost/Tor tools separated into `~/Tools/ProPlus-Arsenal`

## Start Docker

    cd ~/Projects/ProPlus/data_analytics
    make up

Expected:

api, mongo, and redis should become healthy.

## Stop Docker

    make down

## Full Local Verification

Run:

    make ci-local

This executes:

- ruff lint
- pytest
- OpenAPI summary
- health checks
- auth smoke
- admin smoke

Expected:

    PROPLUS SMOKE TEST PASSED
    PROPLUS ADMIN SMOKE TEST PASSED

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

## Structured Errors

The API returns structured error responses.

Example:

    {
      "error": {
        "code": "http_error",
        "message": "No bearer token",
        "status_code": 401,
        "request_id": "example-request-id"
      }
    }

Validation errors include:

    "code": "validation_error"

and a `details` list.

## Request ID

Every response includes:

    X-Request-ID

If the request provides `X-Request-ID`, the response echoes it. Otherwise, the API generates one.

## Safety Rules

Never commit:

- .env
- secrets/
- *.pem
- *.key
- *.asc
- *.gpg
- payloads
- quarantine artifacts
- generated reports
- generated dumps
- local Arsenal tools

Arsenal path:

    ~/Tools/ProPlus-Arsenal

Local JWT keys:

    secrets/jwt_private.pem
    secrets/jwt_public.pem

## Completed Phases

- PHASE 1A — Backend auth boot stabilized
- PHASE 1B — Readiness and smoke hardening
- PHASE 1C — Docker backend boot hardening
- PHASE 1D — API security polish
- PHASE 1E — Developer experience and API documentation polish
- PHASE 1F — GitHub CI guard
- PHASE 1G — Quality gates and artifact cleanup
- PHASE 1H — API/auth/admin test armor
- PHASE 1I Part 1 — Structured errors and request IDs
- PHASE 1I Part 2 — Config validation coverage

## Next Recommended Work

Continue PHASE 1I with one small branch at a time.

Recommended next items:

- README/API docs polish
- CI log artifact polish
- warning cleanup strategy
- rate-limit behavior tests
- audit event tests

## Makefile Command Center

Recommended daily start:

    make up
    make ci-local

Check status:

    make status

View API logs:

    make logs

Stop stack only when finished:

    make down

Important rule:

Do not run all Makefile commands in one line. In particular, do not run `make down` before `make health`, `make smoke`, `make admin-smoke`, or `make test-all`.

Correct:

    make up
    make ci-local

Incorrect:

    make up
    make down
    make test-all
