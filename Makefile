SHELL := /usr/bin/env bash
.RECIPEPREFIX := >

API ?= http://127.0.0.1:8000

.PHONY: up down restart ps logs wait-api health smoke admin-smoke test-all status openapi lint test quality ci-local

up:
>docker compose up -d
>$(MAKE) wait-api

down:
>docker compose down

restart:
>docker compose restart api
>$(MAKE) wait-api

ps:
>docker compose ps

logs:
>docker compose logs --tail=120 api

wait-api:
>@echo "👑 Waiting for API health..."
>@for i in {1..90}; do \
>  STATUS="$$(docker inspect -f '{{.State.Health.Status}}' data_analytics-api-1 2>/dev/null || echo starting)"; \
>  echo "api health: $$STATUS"; \
>  if [ "$$STATUS" = "healthy" ]; then exit 0; fi; \
>  sleep 2; \
>done; \
>echo "❌ API did not become healthy"; \
>docker compose ps; \
>echo "👑 API LOGS"; \
>docker compose logs --tail=200 api; \
>echo "👑 MONGO LOGS"; \
>docker compose logs --tail=120 mongo; \
>echo "👑 REDIS LOGS"; \
>docker compose logs --tail=120 redis; \
>exit 1

health:
>curl -fsS $(API)/healthz; echo
>curl -fsS $(API)/readyz; echo

smoke:
>API="$(API)" ./scripts/smoke.sh

admin-smoke:
>export MONGO_URL="mongodb://localhost:27017/proplus"; \
>export REDIS_URL="redis://localhost:6379/0"; \
>export PRIVATE_KEY_PATH="secrets/jwt_private.pem"; \
>export PUBLIC_KEY_PATH="secrets/jwt_public.pem"; \
>export EMAIL_DEV_MODE="true"; \
>API="$(API)" ./scripts/admin_smoke.sh

test-all:
>$(MAKE) health
>$(MAKE) smoke
>$(MAKE) admin-smoke

status:
>git status --short
>docker compose ps


openapi:
>curl -fsS $(API)/openapi.json -o /tmp/proplus_openapi.json
>./scripts/openapi_summary.py /tmp/proplus_openapi.json


lint:
>ruff check app scripts tests --select E,F --ignore E501

test:
>pytest

quality:
>$(MAKE) lint
>$(MAKE) test

ci-local:
>$(MAKE) quality
>$(MAKE) openapi
>$(MAKE) test-all
