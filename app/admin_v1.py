import time

from bson import ObjectId
from fastapi import APIRouter, Body, Depends, HTTPException, Query

from .core.admin_deps import admin_required
from .db import auth_events, users

router = APIRouter(dependencies=[Depends(admin_required)])


def parse_object_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=400, detail="invalid object id")
    return ObjectId(value)


@router.get("/users")
async def list_users(
    q: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=200),
):
    skip = (page - 1) * limit
    filt = {"email": {"$regex": q, "$options": "i"}} if q else {}

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
    oid = parse_object_id(uid)
    u = await users.find_one({"_id": oid})

    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(u["_id"]),
        "email": u["email"],
        "role": u.get("role", "user"),
        "email_verified": u.get("email_verified", False),
        "locked_until": u.get("locked_until", 0),
        "created_at": u.get("created_at", 0),
    }


@router.post("/users/{uid}/role")
async def set_role(uid: str, role: str = Body(..., embed=True)):
    oid = parse_object_id(uid)

    if role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="role must be 'admin' or 'user'")

    res = await users.update_one({"_id": oid}, {"$set": {"role": role}})

    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"ok": True, "role": role}


@router.post("/users/{uid}/lock")
async def lock_user(uid: str, minutes: int = Body(15, embed=True)):
    oid = parse_object_id(uid)
    until = int(time.time()) + minutes * 60

    res = await users.update_one({"_id": oid}, {"$set": {"locked_until": until}})

    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"ok": True, "locked_until": until}


@router.post("/users/{uid}/unlock")
async def unlock_user(uid: str):
    oid = parse_object_id(uid)

    res = await users.update_one({"_id": oid}, {"$set": {"locked_until": 0}})

    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"ok": True}


@router.get("/auth-events")
async def list_events(
    kind: str | None = None,
    user_id: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
):
    skip = (page - 1) * limit
    filt = {}

    if kind:
        filt["kind"] = kind

    if user_id:
        filt["user_id"] = user_id

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
