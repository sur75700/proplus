import time
from bson import ObjectId
from fastapi import APIRouter, Depends, Query, Body, HTTPException
from .core.admin_deps import admin_required
from .core.pagination import get_pagination
from .db import users, auth_events

router = APIRouter(dependencies=[Depends(admin_required)])

@router.get("/users")
async def list_users(q: str | None = None, page: int = Query(1, ge=1), limit: int = Query(25, ge=1, le=200)):
    skip = (page - 1) * limit
    filt = {}
    if q:
        filt = {"email": {"$regex": q, "$options": "i"}}
    total = await users.count_documents(filt)
    cursor = users.find(filt).sort("created_at", -1).skip(skip).limit(limit)
    data = []
    async for u in cursor:
        data.append({
            "id": str(u["_id"]),
            "email": u["email"],
            "role": u.get("role", "user"),
            "email_verified": u.get("email_verified", False),
            "locked_until": u.get("locked_until", 0),
            "created_at": u.get("created_at", 0),
        })
    return {"total": total, "page": page, "limit": limit, "items": data}

@router.get("/users/{uid}")
async def get_user(uid: str):
    u = await users.find_one({"_id": ObjectId(uid)})
    if not u: raise HTTPException(404, "User not found")
    return {
        "id": str(u["_id"]), "email": u["email"], "role": u.get("role","user"),
        "email_verified": u.get("email_verified", False), "locked_until": u.get("locked_until", 0),
        "created_at": u.get("created_at", 0),
    }

@router.post("/users/{uid}/role")
async def set_role(uid: str, role: str = Body(..., embed=True)):
    if role not in ("admin", "user"):
        raise HTTPException(400, "role must be 'admin' or 'user'")
    res = await users.update_one({"_id": ObjectId(uid)}, {"$set": {"role": role}})
    if res.matched_count == 0: raise HTTPException(404, "User not found")
    return {"ok": True, "role": role}

@router.post("/users/{uid}/lock")
async def lock_user(uid: str, minutes: int = Body(15, embed=True)):
    until = int(time.time()) + minutes*60
    res = await users.update_one({"_id": ObjectId(uid)}, {"$set": {"locked_until": until}})
    if res.matched_count == 0: raise HTTPException(404, "User not found")
    return {"ok": True, "locked_until": until}

@router.post("/users/{uid}/unlock")
async def unlock_user(uid: str):
    res = await users.update_one({"_id": ObjectId(uid)}, {"$set": {"locked_until": 0}})
    if res.matched_count == 0: raise HTTPException(404, "User not found")
    return {"ok": True}

@router.get("/auth-events")
async def list_events(kind: str | None = None, user_id: str | None = None, page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=500)):
    skip = (page - 1) * limit
    filt = {}
    if kind: filt["kind"] = kind
    if user_id: filt["user_id"] = user_id
    total = await auth_events.count_documents(filt)
    cursor = auth_events.find(filt).sort("ts", -1).skip(skip).limit(limit)
    items = []
    async for e in cursor:
        items.append({
            "ts": e.get("ts", 0),
            "kind": e.get("kind"),
            "user_id": e.get("user_id"),
            "meta": e.get("meta", {}),
        })
    return {"total": total, "page": page, "limit": limit, "items": items}
