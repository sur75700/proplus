# ProPlus API

ProPlus API is a FastAPI backend platform with MongoDB, Redis, RS256 JWT authentication, admin RBAC, structured error responses, request ID tracing, health/readiness checks, Docker Compose boot, GitHub Actions CI, and professional smoke tests.

## Current Status

Royal stable backend core.

Current checkpoint:

- Branch: `main`
- Phase: `PHASE 1I — Backend Production Hardening`
- CI: GitHub Actions green
- Local test suite: 37 pytest tests
- Quality gates: ruff + pytest
- Full local verification: `make ci-local`

Implemented:

- FastAPI application
- MongoDB integration
- Redis integration
- Docker Compose stack
- RS256 JWT access tokens
- refresh token rotation
- refresh token reuse detection
- logout token revocation
- email verification flow
- password reset flow
- admin RBAC
- Mongo indexes
- system readiness checks
- structured error responses
- `X-Request-ID` response tracing
- OpenAPI documentation polish
- auth smoke test
- admin smoke test
- API route contract tests
- schema validation tests
- JWT/security utility tests
- auth endpoint integration tests
- admin endpoint integration tests
- config validation tests
- Makefile command center
- clean product repo policy

## Stack

- Python 3.11
- FastAPI
- MongoDB
- Redis
- Docker Compose
- python-jose
- passlib / bcrypt
- Pydantic settings
- pytest
- ruff
- GitHub Actions

## Quick Start

Start the stack:

    make up

Run the full local verification chain:

    make ci-local

Run quality only:

    make quality

Run smoke tests only:

    make test-all

Check status:

    make status

View API logs:

    make logs

Stop the stack:

    make down

## API URLs

Local API:

    http://127.0.0.1:8000

Swagger UI:

    http://127.0.0.1:8000/docs

ReDoc:

    http://127.0.0.1:8000/redoc

OpenAPI JSON:

    http://127.0.0.1:8000/openapi.json

## Health Checks

Liveness:

    GET /healthz

Readiness:

    GET /readyz

Readiness checks MongoDB and Redis.

Expected healthy readiness response:

    {"ready":true,"checks":{"mongo":true,"redis":true}}

## Structured Errors

HTTP and validation errors use a structured response shape.

Example:

    {
      "error": {
        "code": "http_error",
        "message": "No bearer token",
        "status_code": 401,
        "request_id": "example-request-id"
      }
    }

Validation errors use:

    {
      "error": {
        "code": "validation_error",
        "message": "Request validation failed",
        "status_code": 422,
        "request_id": "example-request-id",
        "details": []
      }
    }

Every response includes:

    X-Request-ID

If the client sends `X-Request-ID`, the API returns the same value. Otherwise, the API generates one.

## Auth Endpoints

- POST /auth/register
- POST /auth/login
- GET /auth/me
- POST /auth/refresh
- POST /auth/logout
- POST /auth/verify/send
- POST /auth/verify/confirm
- POST /auth/password/forgot
- POST /auth/password/reset

Security behavior:

- invalid access token returns 401
- old refresh token reuse returns 401
- refresh token reuse revokes active refresh chain
- smoke tests do not print JWT token values

## Admin Endpoints

- GET /admin/users
- GET /admin/users/{uid}
- POST /admin/users/{uid}/role
- POST /admin/users/{uid}/lock
- POST /admin/users/{uid}/unlock
- GET /admin/auth-events

Admin security behavior:

- no token -> 401
- bad token -> 401
- normal user admin access -> 403
- admin user access -> 200
- bad ObjectId -> 400

## Developer Commands

Start:

    make up

Full local CI:

    make ci-local

Quality gates:

    make quality

Auth smoke:

    make smoke

Admin smoke:

    make admin-smoke

OpenAPI summary:

    make openapi

Logs:

    make logs

Status:

    make status

Stop:

    make down

Important:

Do not run all Makefile commands in one line. In particular, do not run `make down` before health, smoke, admin-smoke, or test-all.

Correct:

    make up
    make ci-local

Incorrect:

    make up
    make down
    make test-all

## Documentation

- docs/dev-runbook.md
- docs/api.md

## Local Secrets and Artifact Policy

Never commit:

- .env
- secrets/
- private keys
- payloads
- quarantine artifacts
- generated dumps
- generated reports
- local Arsenal tools

Expected local JWT files:

- secrets/jwt_private.pem
- secrets/jwt_public.pem

Docker uses:

- PRIVATE_KEY_PATH=/run/secrets/jwt_private_key
- PUBLIC_KEY_PATH=/run/secrets/jwt_public_key

Ghost/Tor/local helper tools are separated from the product repository and kept under:

    ~/Tools/ProPlus-Arsenal

## Current Phase

PHASE 1I — Backend Production Hardening

Completed checkpoints include:

- backend auth boot stabilization
- readiness checks
- Docker hardening
- smoke test hardening
- admin RBAC hardening
- refresh token reuse detection
- OpenAPI polish
- API guide
- Makefile command center
- GitHub Actions CI
- generated artifact cleanup
- API contract tests
- JWT/security utility tests
- auth endpoint integration tests
- admin endpoint integration tests
- structured error responses
- request ID middleware
- config validation coverage
