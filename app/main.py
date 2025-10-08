from fastapi import FastAPI

# Routers
from .auth_v2 import router as auth_router
from .admin_v1 import router as admin_router

app = FastAPI(title="ProPlus API")

@app.get("/healthz")
async def healthz():
    return {"ok": True}

# Mount routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
