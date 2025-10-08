import time, uuid, hashlib
from fastapi import APIRouter, HTTPException, Header, Body, Request, status
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId

from .schemas import RegisterIn, LoginIn, TokenOut, MeOut
from .models import create_user, get_user_by_email, verify_password, get_user_by_id, hash_password
from .core.jwt_utils import create_access, create_refresh, decode_token, is_refresh
from .db import refresh_tokens, auth_events, users
from .core.security_utils import rate_limit_or_429, track_login_fail, reset_login_fail, fingerprint_from_request
from .core.token_store import create_email_verify_token, verify_email_token, create_reset_token, use_reset_token
from .core.emailer import send_email
from .core.config import settings

router = APIRouter()
def jti_hash(jti: str) -> str: return hashlib.sha256(jti.encode()).hexdigest()
async def log_event(kind: str, user_id: str | None, meta: dict): await auth_events.insert_one({"ts": int(time.time()), "kind": kind, "user_id": user_id, "meta": meta})
def _extract_bearer(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "): raise HTTPException(401, "No bearer token")
    return authorization.split(" ", 1)[1]

@router.post("/register", status_code=201)
async def register(payload: RegisterIn, request: Request):
    uid = await create_user(payload.email, payload.password)
    if not uid: raise HTTPException(409, "email already exists")
    token = await create_email_verify_token(uid, payload.email)
    url = f"{settings.frontend_base_url}/verify-email?token={token}"
    await send_email(payload.email, "Verify your email — ProPlus", f"<p>Verify:</p><p><a href='{url}'>Open</a></p>")
    await log_event("register", uid, {"verify_sent": True})
    return {"id": uid, "email": payload.email, "verify_sent": True}

@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, request: Request):
    ip = request.client.host if request.client else "unknown"
    await rate_limit_or_429(f"rl:login:ip:{ip}", 20, 60)
    await rate_limit_or_429(f"rl:login:user:{payload.email.lower()}", 10, 60)

    user = await get_user_by_email(payload.email)
    if not user: raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    if user.get("locked_until",0) > int(time.time()): raise HTTPException(403, "account temporarily locked")
    if not verify_password(payload.password, user["password_hash"]):
        if await track_login_fail(payload.email): await users.update_one({"_id": user["_id"]}, {"$set":{"locked_until": int(time.time())+900}})
        await log_event("login_fail", str(user["_id"]), {}); raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")

    await reset_login_fail(payload.email)
    if user.get("locked_until",0)>0: await users.update_one({"_id": user["_id"]}, {"$set":{"locked_until":0}})
    sub = str(user["_id"]); jti = str(uuid.uuid4())
    access = create_access(sub); refresh = create_refresh(sub, jti)
    await refresh_tokens.insert_one({"user_id": ObjectId(sub), "jti_hash": jti_hash(jti), "issued_at": int(time.time()), "expires_at": int(time.time())+30*24*3600, "fp": fingerprint_from_request(request), "revoked": False})
    await log_event("login_success", sub, {})
    return {"access_token": access, "refresh_token": refresh, "token_type":"bearer"}

@router.get("/me", response_model=MeOut)
async def me(authorization: str = Header(None)):
    payload = decode_token(_extract_bearer(authorization)); uid = payload.get("sub")
    u = await get_user_by_id(uid)
    if not u: raise HTTPException(401, "invalid token user")
    return {"id": str(u["_id"]), "email": u["email"]}

@router.post("/refresh", response_model=TokenOut)
async def refresh_token(request: Request, refresh_token: str = Body(..., embed=True)):
    payload = decode_token(refresh_token)
    if not is_refresh(payload): raise HTTPException(400, "not a refresh token")
    h = jti_hash(payload["jti"])
    doc = await refresh_tokens.find_one({"jti_hash": h, "revoked": False})
    if not doc: raise HTTPException(401, "refresh invalid or revoked")
    await refresh_tokens.update_one({"_id": doc["_id"]}, {"$set":{"revoked": True, "revoked_at": int(time.time())}})
    sub = payload["sub"]; new_jti = str(uuid.uuid4())
    new_refresh = create_refresh(sub, new_jti)
    await refresh_tokens.insert_one({"user_id": ObjectId(sub), "jti_hash": jti_hash(new_jti), "issued_at": int(time.time()), "expires_at": int(time.time())+30*24*3600, "fp": fingerprint_from_request(request), "revoked": False})
    new_access = create_access(sub); await log_event("refresh", sub, {})
    return {"access_token": new_access, "refresh_token": new_refresh, "token_type":"bearer"}

@router.post("/logout", status_code=204)
async def logout(refresh_token: str = Body(..., embed=True)):
    payload = decode_token(refresh_token)
    if not is_refresh(payload): raise HTTPException(400, "not a refresh token")
    await refresh_tokens.update_one({"jti_hash": jti_hash(payload["jti"])}, {"$set":{"revoked": True, "revoked_at": int(time.time())}})
    await log_event("logout", payload["sub"], {}); return

# Email verify
@router.post("/verify/send", status_code=202)
async def send_verify(email: EmailStr = Body(..., embed=True)):
    user = await get_user_by_email(email); 
    if not user: raise HTTPException(404, "user not found")
    token = await create_email_verify_token(str(user["_id"]), email)
    url = f"{settings.frontend_base_url}/verify-email?token={token}"
    await send_email(email, "Verify your email — ProPlus", f"<p>Verify:</p><p><a href='{url}'>Open</a></p>")
    await log_event("verify_sent", str(user["_id"]), {}); return {"sent": True}

@router.post("/verify/confirm", status_code=200)
async def confirm_verify(token: str = Body(..., embed=True)):
    doc = await verify_email_token(token)
    if not doc: raise HTTPException(400, "invalid or expired token")
    await users.update_one({"_id": ObjectId(doc["user_id"])}, {"$set":{"email_verified": True}})
    await log_event("verify_ok", doc["user_id"], {}); return {"verified": True}

# Password reset
class ResetPerform(BaseModel):
    token: str
    new_password: str = Field(min_length=10, max_length=128)

@router.post("/password/forgot", status_code=202)
async def password_forgot(email: EmailStr = Body(..., embed=True)):
    user = await get_user_by_email(email)
    if user:
        token = await create_reset_token(str(user["_id"]), user["email"])
        url = f"{settings.frontend_base_url}/reset-password?token={token}"
        await send_email(user["email"], "Reset your password — ProPlus", f"<p>Reset:</p><p><a href='{url}'>Open</a></p>")
        await log_event("reset_sent", str(user["_id"]), {})
    return {"sent": True}

@router.post("/password/reset", status_code=200)
async def password_reset(payload: ResetPerform):
    doc = await use_reset_token(payload.token)
    if not doc: raise HTTPException(400, "invalid or expired token")
    await users.update_one({"_id": ObjectId(doc["user_id"])}, {"$set":{"password_hash": hash_password(payload.new_password)}})
    await log_event("reset_ok", doc["user_id"], {}); return {"reset": True}

# --------------------------------------------------------------------
# Email verification + password reset endpoints
# --------------------------------------------------------------------

@router.post("/verify/send", status_code=202)
async def send_verify(email: EmailStr = Body(..., embed=True)):
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(404, "user not found")
    token = await create_email_verify_token(str(user["_id"]), email)
    url = f"{settings.frontend_base_url}/verify-email?token={token}"
    await send_email(email, "Verify your email — ProPlus", f"<p>Verify:</p><p><a href='{url}'>Open</a></p>")
    await log_event("verify_sent", str(user["_id"]), {})
    return {"sent": True}

@router.post("/verify/confirm", status_code=200)
async def confirm_verify(token: str = Body(..., embed=True)):
    doc = await verify_email_token(token)
    if not doc:
        raise HTTPException(400, "invalid or expired token")
    await users.update_one({"_id": ObjectId(doc["user_id"])}, {"$set": {"email_verified": True}})
    await log_event("verify_ok", doc["user_id"], {})
    return {"verified": True}


# Password reset ------------------------------------------------------

class ResetPerform(BaseModel):
    token: str
    new_password: str = Field(min_length=10, max_length=128)

@router.post("/password/forgot", status_code=202)
async def password_forgot(email: EmailStr = Body(..., embed=True)):
    user = await get_user_by_email(email)
    if user:
        token = await create_reset_token(str(user["_id"]), user["email"])
        url = f"{settings.frontend_base_url}/reset-password?token={token}"
        await send_email(user["email"], "Reset your password — ProPlus", f"<p>Reset:</p><p><a href='{url}'>Open</a></p>")
        await log_event("reset_sent", str(user["_id"]), {})
    return {"sent": True}

@router.post("/password/reset", status_code=200)
async def password_reset(payload: ResetPerform):
    doc = await use_reset_token(payload.token)
    if not doc:
        raise HTTPException(400, "invalid or expired token")
    await users.update_one(
        {"_id": ObjectId(doc["user_id"])},
        {"$set": {"password_hash": hash_password(payload.new_password)}}
    )
    await log_event("reset_ok", doc["user_id"], {})
    return {"reset": True}
