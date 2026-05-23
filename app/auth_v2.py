import hashlib
import time
import uuid

from bson import ObjectId
from fastapi import APIRouter, Body, Header, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from jose import JWTError

from .core.config import settings
from .core.emailer import send_email
from .core.jwt_utils import create_access, create_refresh, decode_token, is_refresh
from .core.security_utils import (
    fingerprint_from_request,
    rate_limit_or_429,
    reset_login_fail,
    track_login_fail,
)
from .core.token_store import (
    create_email_verify_token,
    create_reset_token,
    use_reset_token,
    verify_email_token,
)
from .db import auth_events, refresh_tokens, users
from .models import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    hash_password,
    verify_password,
)
from .schemas import LoginIn, MeOut, RegisterIn, TokenOut

router = APIRouter()


class ResetPerform(BaseModel):
    token: str
    new_password: str = Field(min_length=10, max_length=128)


def jti_hash(jti: str) -> str:
    return hashlib.sha256(jti.encode()).hexdigest()


async def log_event(kind: str, user_id: str | None, meta: dict) -> None:
    await auth_events.insert_one(
        {
            "ts": int(time.time()),
            "kind": kind,
            "user_id": user_id,
            "meta": meta,
        }
    )


def _extract_bearer(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No bearer token")
    return authorization.split(" ", 1)[1]


def _decode_or_401(token: str) -> dict:
    try:
        return decode_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="invalid token")


@router.post("/register", status_code=201)
async def register(payload: RegisterIn, request: Request):
    uid = await create_user(payload.email, payload.password)
    if not uid:
        raise HTTPException(status_code=409, detail="email already exists")

    token = await create_email_verify_token(uid, payload.email)
    url = f"{settings.frontend_base_url}/verify-email?token={token}"

    await send_email(
        payload.email,
        "Verify your email — ProPlus",
        f"<p>Verify:</p><p><a href='{url}'>Open</a></p>",
    )
    await log_event("register", uid, {"verify_sent": True})

    return {"id": uid, "email": payload.email, "verify_sent": True}


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, request: Request):
    ip = request.client.host if request.client else "unknown"

    await rate_limit_or_429(f"rl:login:ip:{ip}", 20, 60)
    await rate_limit_or_429(f"rl:login:user:{payload.email.lower()}", 10, 60)

    user = await get_user_by_email(payload.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")

    if user.get("locked_until", 0) > int(time.time()):
        raise HTTPException(status_code=403, detail="account temporarily locked")

    if not verify_password(payload.password, user["password_hash"]):
        should_lock = await track_login_fail(payload.email)
        if should_lock:
            await users.update_one(
                {"_id": user["_id"]},
                {"$set": {"locked_until": int(time.time()) + 900}},
            )
        await log_event("login_fail", str(user["_id"]), {})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")

    await reset_login_fail(payload.email)

    if user.get("locked_until", 0) > 0:
        await users.update_one({"_id": user["_id"]}, {"$set": {"locked_until": 0}})

    sub = str(user["_id"])
    jti = str(uuid.uuid4())

    access = create_access(sub)
    refresh = create_refresh(sub, jti)

    await refresh_tokens.insert_one(
        {
            "user_id": ObjectId(sub),
            "jti_hash": jti_hash(jti),
            "issued_at": int(time.time()),
            "expires_at": int(time.time()) + settings.refresh_exp_days * 24 * 3600,
            "fp": fingerprint_from_request(request),
            "revoked": False,
        }
    )

    await log_event("login_success", sub, {})

    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
    }


@router.get("/me", response_model=MeOut)
async def me(authorization: str = Header(None)):
    payload = _decode_or_401(_extract_bearer(authorization))
    uid = payload.get("sub")

    u = await get_user_by_id(uid)
    if not u:
        raise HTTPException(status_code=401, detail="invalid token user")

    return {"id": str(u["_id"]), "email": u["email"]}


@router.post("/refresh", response_model=TokenOut)
async def refresh_token(request: Request, refresh_token: str = Body(..., embed=True)):
    payload = _decode_or_401(refresh_token)
    if not is_refresh(payload):
        raise HTTPException(status_code=400, detail="not a refresh token")

    sub = payload.get("sub")
    jti = payload.get("jti")

    if not sub or not ObjectId.is_valid(sub) or not jti:
        raise HTTPException(status_code=401, detail="refresh invalid")

    h = jti_hash(jti)
    doc = await refresh_tokens.find_one({"jti_hash": h})

    if not doc:
        await log_event("refresh_invalid", sub, {"reason": "unknown_jti"})
        raise HTTPException(status_code=401, detail="refresh invalid or revoked")

    if doc.get("revoked"):
        await refresh_tokens.update_many(
            {"user_id": ObjectId(sub), "revoked": False},
            {"$set": {"revoked": True, "revoked_at": int(time.time()), "revoked_reason": "reuse_detected"}},
        )
        await log_event(
            "refresh_reuse",
            sub,
            {
                "jti_hash": h,
                "fp": fingerprint_from_request(request),
            },
        )
        raise HTTPException(status_code=401, detail="refresh token reuse detected")

    if doc.get("expires_at", 0) < int(time.time()):
        await refresh_tokens.update_one(
            {"_id": doc["_id"]},
            {"$set": {"revoked": True, "revoked_at": int(time.time()), "revoked_reason": "expired"}},
        )
        await log_event("refresh_expired", sub, {"jti_hash": h})
        raise HTTPException(status_code=401, detail="refresh expired")

    await refresh_tokens.update_one(
        {"_id": doc["_id"]},
        {"$set": {"revoked": True, "revoked_at": int(time.time()), "revoked_reason": "rotated"}},
    )

    new_jti = str(uuid.uuid4())
    new_refresh = create_refresh(sub, new_jti)

    await refresh_tokens.insert_one(
        {
            "user_id": ObjectId(sub),
            "jti_hash": jti_hash(new_jti),
            "issued_at": int(time.time()),
            "expires_at": int(time.time()) + settings.refresh_exp_days * 24 * 3600,
            "fp": fingerprint_from_request(request),
            "revoked": False,
        }
    )

    new_access = create_access(sub)
    await log_event("refresh", sub, {})

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


@router.post("/logout", status_code=204)
async def logout(refresh_token: str = Body(..., embed=True)):
    payload = _decode_or_401(refresh_token)
    if not is_refresh(payload):
        raise HTTPException(status_code=400, detail="not a refresh token")

    await refresh_tokens.update_one(
        {"jti_hash": jti_hash(payload["jti"])},
        {"$set": {"revoked": True, "revoked_at": int(time.time())}},
    )

    await log_event("logout", payload["sub"], {})
    return None


@router.post("/verify/send", status_code=202)
async def send_verify(email: EmailStr = Body(..., embed=True)):
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    token = await create_email_verify_token(str(user["_id"]), email)
    url = f"{settings.frontend_base_url}/verify-email?token={token}"

    await send_email(
        email,
        "Verify your email — ProPlus",
        f"<p>Verify:</p><p><a href='{url}'>Open</a></p>",
    )
    await log_event("verify_sent", str(user["_id"]), {})

    return {"sent": True}


@router.post("/verify/confirm", status_code=200)
async def confirm_verify(token: str = Body(..., embed=True)):
    doc = await verify_email_token(token)
    if not doc:
        raise HTTPException(status_code=400, detail="invalid or expired token")

    await users.update_one(
        {"_id": ObjectId(doc["user_id"])},
        {"$set": {"email_verified": True}},
    )
    await log_event("verify_ok", doc["user_id"], {})

    return {"verified": True}


@router.post("/password/forgot", status_code=202)
async def password_forgot(email: EmailStr = Body(..., embed=True)):
    user = await get_user_by_email(email)

    if user:
        token = await create_reset_token(str(user["_id"]), user["email"])
        url = f"{settings.frontend_base_url}/reset-password?token={token}"

        await send_email(
            user["email"],
            "Reset your password — ProPlus",
            f"<p>Reset:</p><p><a href='{url}'>Open</a></p>",
        )
        await log_event("reset_sent", str(user["_id"]), {})

    return {"sent": True}


@router.post("/password/reset", status_code=200)
async def password_reset(payload: ResetPerform):
    doc = await use_reset_token(payload.token)
    if not doc:
        raise HTTPException(status_code=400, detail="invalid or expired token")

    await users.update_one(
        {"_id": ObjectId(doc["user_id"])},
        {"$set": {"password_hash": hash_password(payload.new_password)}},
    )
    await log_event("reset_ok", doc["user_id"], {})

    return {"reset": True}
