# ProPlus API Guide

## Overview

ProPlus API is a FastAPI backend with MongoDB, Redis, RS256 JWT authentication, refresh-token rotation, admin RBAC, readiness checks, and smoke tests.

## Base URL

Local Docker:

http://127.0.0.1:8000

Interactive docs:

http://127.0.0.1:8000/docs

OpenAPI JSON:

http://127.0.0.1:8000/openapi.json

## System Endpoints

GET /healthz

Purpose:
Lightweight liveness check.

Expected response:

{"ok":true,"service":"proplus-api"}

GET /readyz

Purpose:
Dependency readiness check for MongoDB and Redis.

Expected response:

{"ready":true,"checks":{"mongo":true,"redis":true}}

## Auth Flow

POST /auth/register

Creates a new user and sends an email verification link. In local development, email is logged because EMAIL_DEV_MODE=true.

POST /auth/login

Returns:

- access_token
- refresh_token
- token_type

GET /auth/me

Requires:

Authorization: Bearer ACCESS_TOKEN

Returns the current authenticated user.

POST /auth/refresh

Accepts refresh_token and returns a rotated access/refresh token pair.

Security behavior:
Reusing an old refresh token returns 401 and revokes the active refresh chain.

POST /auth/logout

Accepts refresh_token and revokes it.

POST /auth/verify/send

Sends verification email.

POST /auth/verify/confirm

Confirms email verification token.

POST /auth/password/forgot

Sends password reset email.

POST /auth/password/reset

Resets password using reset token.

## Admin Flow

Admin endpoints require:

Authorization: Bearer ADMIN_ACCESS_TOKEN

GET /admin/users

Lists users.

GET /admin/users/{uid}

Returns one user.

POST /admin/users/{uid}/role

Changes user role to admin or user.

POST /admin/users/{uid}/lock

Locks a user for a number of minutes.

POST /admin/users/{uid}/unlock

Unlocks a user.

GET /admin/auth-events

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

Run all checks:

make test-all

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
make test-all

Do not run make down before smoke/test commands.

## Safety Rules

Never commit:

- .env
- secrets/
- private keys
- payloads
- quarantine artifacts
- local Arsenal tools
