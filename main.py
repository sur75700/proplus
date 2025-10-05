from fastapi import FastAPI

from db import connect_db, close_db
from health import router as health_router
from auth import router as auth_router
from projects import router as projects_router

app = FastAPI(title="ProPlus")


@app.on_event("startup")
async def on_start():
    await connect_db()


@app.on_event("shutdown")
async def on_stop():
    await close_db()


app.include_router(health_router)  # /healthz
app.include_router(auth_router)
app.include_router(projects_router)  # /projects


@app.get("/")
def root():
    return {"status": "ok", "app": "ProPlus"}
