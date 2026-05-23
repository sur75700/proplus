# ProPlus API

ProPlus API is a FastAPI backend platform with MongoDB, Redis, RS256 JWT authentication, admin RBAC, health checks, Docker Compose boot, and professional smoke tests.

## Current Status

Royal stable backend core.

Implemented:

- FastAPI application
- MongoDB integration
- Redis integration
- Docker Compose stack
- RS256 JWT access tokens
- refresh token rotation
- refresh token reuse detection
- logout token revocation
- admin RBAC
- Mongo indexes
- system readiness checks
- OpenAPI documentation polish
- auth smoke test
- admin smoke test
- Makefile command center

## Stack

- Python 3.11
- FastAPI
- MongoDB
- Redis
- Docker Compose
- python-jose
- passlib / bcrypt
- Pydantic settings

## Quick Start

Start the stack:

    make up

Run all checks:

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

Run all tests:

    make test-all

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
    make test-all

Incorrect:

    make up
    make down
    make test-all

## Documentation

- docs/dev-runbook.md
- docs/api.md

## Local Secrets

Never commit:

- .env
- secrets/
- private keys
- payloads
- quarantine artifacts
- local Arsenal tools

Expected local JWT files:

- secrets/jwt_private.pem
- secrets/jwt_public.pem

Docker uses:

- PRIVATE_KEY_PATH=/run/secrets/jwt_private_key
- PUBLIC_KEY_PATH=/run/secrets/jwt_public_key

## Current Phase

PHASE 1E — Developer Experience and API Documentation Polish

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
