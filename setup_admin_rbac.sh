set -e

# ensure dirs
mkdir -p app/core app/scripts

# 1) requirements (ավելացնենք, եթե պետք է)
if ! grep -q "pydantic-settings" requirements.txt 2>/dev/null; then
  echo "pydantic-settings==2.4.0" >> requirements.txt
fi
if ! grep -q "aioredis" requirements.txt 2>/dev/null; then
  echo "aioredis==2.0.1" >> requirements.txt
fi
if ! grep -q "aiosmtplib" requirements.txt 2>/dev/null; then
  echo "aiosmtplib==2.0.2" >> requirements.txt
fi

# 2) admin deps
cat > app/core/admin_deps.py <<'PY'
from fastapi import Depends, HTTPException, Header
from jose import JWTError
from ..core.jwt_utils import decode_token
from ..models import get_user_by_id

async def admin_required(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "No bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(401, "Invalid token")
    uid = payload.get("sub")
    user = await get_user_by_id(uid)
    if not user:
        raise HTTPException(401, "User not found")
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin only")
    return user
PY

# 3) pagination helper
cat > app/core/pagination.py <<'PY'
from fastapi import Query

def get_pagination(page: int = Query(1, ge=1), limit: int = Query(25, ge=1, le=200)):
    skip = (page - 1) * limit
    return {"page": page, "limit": limit, "skip": skip}
PY

# 4) admin router
cat > app/admin_v1.py <<'PY'
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
PY

# 5) models.py — ensure role default = user
# only patch minimal: if file exists, ensure 'role' is set in create_user
if grep -q "def create_user" app/models.py; then
  # insert role if missing
  if ! grep -q '"role": "user"' app/models.py; then
    sed -i 's/"email_verified": False,/"email_verified": False,\n        "role": "user",/g' app/models.py
  fi
fi

# 6) main.py — include admin router
if ! grep -q "admin_v1" app/main.py; then
  # add import
  sed -i '1,/^from fastapi import FastAPI/ s/^from fastapi import FastAPI.*/from fastapi import FastAPI\nfrom fastapi.middleware.cors import CORSMiddleware\nfrom .auth_v2 import router as auth_router\nfrom .admin_v1 import router as admin_router/' app/main.py
  # add include if missing
  if ! grep -q "admin_router" app/main.py; then
    printf '\napp.include_router(admin_router, prefix="/admin", tags=["admin"])\n' >> app/main.py
  fi
fi

# 7) seed admin script
mkdir -p scripts
cat > scripts/seed_admin.py <<'PY'
import asyncio, sys
from app.models import get_user_by_email, create_user
from app.db import users

ADMIN_EMAIL = sys.argv[1] if len(sys.argv) > 1 else "admin@proplus.com"
ADMIN_PASS  = sys.argv[2] if len(sys.argv) > 2 else "AdminPassword123!"

async def main():
    u = await get_user_by_email(ADMIN_EMAIL)
    if not u:
        uid = await create_user(ADMIN_EMAIL, ADMIN_PASS)
        print("Created:", ADMIN_EMAIL, "id=", uid)
    await users.update_one({"email": ADMIN_EMAIL}, {"$set": {"role": "admin", "email_verified": True}})
    print("Promoted to admin:", ADMIN_EMAIL)

if __name__ == "__main__":
    asyncio.run(main())
PY

echo "✅ Admin RBAC files written. Next steps:"
echo "1) pip install -r requirements.txt   (or docker compose build)"
echo "2) docker compose up -d --build"
echo "3) docker compose exec api python scripts/seed_admin.py admin@proplus.com StrongAdminPass123!"
echo "4) curl admin endpoints with Bearer access token"
