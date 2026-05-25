# ProPlus API Guide

## Overview

ProPlus API is a FastAPI backend with MongoDB, Redis, RS256 JWT authentication, refresh-token rotation, admin RBAC, readiness checks, structured error responses, request ID tracing, smoke tests, and GitHub Actions CI.

## Base URL

Local Docker:

    http://127.0.0.1:8000

Interactive docs:

    http://127.0.0.1:8000/docs

OpenAPI JSON:

    http://127.0.0.1:8000/openapi.json

## System Endpoints

### GET /healthz

Purpose:

Lightweight liveness check.

Expected response:

    {"ok":true,"service":"proplus-api"}

### GET /readyz

Purpose:

Dependency readiness check for MongoDB and Redis.

Expected response:

    {"ready":true,"checks":{"mongo":true,"redis":true}}

If a dependency is unavailable, the endpoint returns 503 with a structured error.

## Request ID

The API supports request tracing with:

    X-Request-ID

Behavior:

- If the client sends `X-Request-ID`, the API returns the same value.
- If the client does not send it, the API generates one.
- Structured errors include the same request ID in the JSON body.

## Structured Error Format

HTTP errors:

    {
      "error": {
        "code": "http_error",
        "message": "No bearer token",
        "status_code": 401,
        "request_id": "example-request-id"
      }
    }

Validation errors:

    {
      "error": {
        "code": "validation_error",
        "message": "Request validation failed",
        "status_code": 422,
        "request_id": "example-request-id",
        "details": []
      }
    }

## Auth Flow

### POST /auth/register

Creates a new user and sends an email verification link. In local development, email is logged because `EMAIL_DEV_MODE=true`.

### POST /auth/login

Returns:

- access_token
- refresh_token
- token_type

### GET /auth/me

Requires:

    Authorization: Bearer ACCESS_TOKEN

Returns the current authenticated user.

### POST /auth/refresh

Accepts `refresh_token` and returns a rotated access/refresh token pair.

Security behavior:

Reusing an old refresh token returns 401 and revokes the active refresh chain.

### POST /auth/logout

Accepts `refresh_token` and revokes it.

### POST /auth/verify/send

Sends verification email.

### POST /auth/verify/confirm

Confirms email verification token.

### POST /auth/password/forgot

Sends password reset email.

### POST /auth/password/reset

Resets password using reset token.

## Admin Flow

Admin endpoints require:

    Authorization: Bearer ADMIN_ACCESS_TOKEN

### GET /admin/users

Lists users.

### GET /admin/users/{uid}

Returns one user.

Invalid ObjectId returns 400.

### POST /admin/users/{uid}/role

Changes user role to `admin` or `user`.

### POST /admin/users/{uid}/lock

Locks a user for a number of minutes.

### POST /admin/users/{uid}/unlock

Unlocks a user.

### GET /admin/auth-events

Lists auth events.

## Admin Security Behavior

Expected behavior:

- no token -> 401
- bad token -> 401
- normal user admin access -> 403
- admin user access -> 200
- bad ObjectId -> 400

## Developer Commands

Start stack:

    make up

Run full local CI:

    make ci-local

Run quality gates:

    make quality

Check health:

    make health

Auth smoke:

    make smoke

Admin smoke:

    make admin-smoke

OpenAPI summary:

    make openapi

View API logs:

    make logs

Stop stack:

    make down

## Daily Workflow

Recommended:

    make up
    make ci-local

Do not run `make down` before smoke/test commands.

## Test Coverage

Current local test suite covers:

- app import
- OpenAPI summary script
- API route contracts
- Pydantic schemas
- JWT utilities
- security utilities
- auth endpoint integration behavior
- admin endpoint integration behavior
- structured error response format
- request ID propagation
- config aliases and defaults

Current expected result:

    37 passed

## Safety Rules

Never commit:

- .env
- secrets/
- private keys
- payloads
- quarantine artifacts
- generated dumps
- generated reports
- local Arsenal tools
