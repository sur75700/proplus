from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from .admin_v1 import router as admin_router
from .auth_v2 import router as auth_router
from .core.error_handlers import install_error_handlers, request_id_middleware
from .core.redis_client import redis
from .db import ensure_indexes, ping_mongo


API_DESCRIPTION = """
ProPlus API is the backend core for the ProPlus product platform.

Current capabilities:
- System health and readiness checks
- JWT authentication with RS256
- Access and refresh token flows
- Refresh-token rotation and reuse detection
- Email verification and password reset flows
- Admin RBAC routes for user management and auth event review

Local development uses Docker Compose with FastAPI, MongoDB, and Redis.
"""


OPENAPI_TAGS = [
    {
        "name": "system",
        "description": "Liveness and readiness endpoints for runtime monitoring.",
    },
    {
        "name": "auth",
        "description": "Registration, login, JWT tokens, email verification, and password reset flows.",
    },
    {
        "name": "admin",
        "description": "Admin-only RBAC endpoints for user management and auth event inspection.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_indexes()
    yield


app = FastAPI(
    title="ProPlus API",
    version="1.0.0-phase1",
    description=API_DESCRIPTION,
    openapi_tags=OPENAPI_TAGS,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.middleware("http")(request_id_middleware)
install_error_handlers(app)


@app.get(
    "/healthz",
    tags=["system"],
    summary="Liveness check",
    description="Returns a lightweight liveness response. This endpoint does not check external dependencies.",
)
async def healthz():
    return {"ok": True, "service": "proplus-api"}


@app.get(
    "/readyz",
    tags=["system"],
    summary="Readiness check",
    description="Checks whether MongoDB and Redis are reachable. Returns 503 if any critical dependency is unavailable.",
)
async def readyz():
    checks = {"mongo": False, "redis": False}

    try:
        checks["mongo"] = await ping_mongo()
    except Exception:
        checks["mongo"] = False

    try:
        checks["redis"] = bool(await redis.ping())
    except Exception:
        checks["redis"] = False

    if not all(checks.values()):
        raise HTTPException(status_code=503, detail={"ready": False, "checks": checks})

    return {"ready": True, "checks": checks}


app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
