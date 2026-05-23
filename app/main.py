from fastapi import FastAPI, HTTPException

from .admin_v1 import router as admin_router
from .auth_v2 import router as auth_router
from .core.redis_client import redis
from .db import ping_mongo

app = FastAPI(title="ProPlus API")


@app.get("/healthz")
async def healthz():
    return {"ok": True, "service": "proplus-api"}


@app.get("/readyz")
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
