set -e

mkdir -p app/core app/scripts secrets

# -------- .env.example --------
cat > .env.example <<'EOF'
MONGO_URL=mongodb://mongo:27017/proplus
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
JWT_ALG=RS256
REDIS_URL=redis://redis:6379/0

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASS=your-app-password
SMTP_FROM=ProPlus <your@gmail.com>

FRONTEND_BASE_URL=http://localhost:3000
API_BASE_URL=http://localhost:8000
EOF

# -------- docker-compose.yml (Redis + secrets) --------
cat > docker-compose.yml <<'EOF'
version: "3.8"
services:
  api:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    volumes:
      - ./app:/app/app
    secrets:
      - jwt_private_key
      - jwt_public_key
    depends_on:
      - mongo
      - redis
  mongo:
    image: mongo:6
    ports: ["27017:27017"]
    volumes: ["mongo_data:/data/db"]
  redis:
    image: redis:7
    ports: ["6379:6379"]

secrets:
  jwt_private_key:
    file: ./secrets/jwt_private.pem
  jwt_public_key:
    file: ./secrets/jwt_public.pem

volumes:
  mongo_data:
EOF

# -------- app/core/config.py --------
cat > app/core/config.py <<'EOF'
from pydantic import BaseSettings

class Settings(BaseSettings):
    mongo_url: str
    access_exp_minutes: int = 15
    refresh_exp_days: int = 30
    jwt_alg: str = "RS256"
    private_key_path: str = "/run/secrets/jwt_private_key"
    public_key_path: str = "/run/secrets/jwt_public_key"

    redis_url: str = "redis://redis:6379/0"
    smtp_host: str = "localhost"
    smtp_port: int = 25
    smtp_user: str | None = None
    smtp_pass: str | None = None
    smtp_from: str = "ProPlus <noreply@proplus.local>"
    frontend_base_url: str = "http://localhost:3000"
    api_base_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"

settings = Settings()
EOF

# -------- app/core/jwt_utils.py --------
cat > app/core/jwt_utils.py <<'EOF'
import time, uuid
from jose import jwt, JWTError
from .config import settings

with open(settings.private_key_path, "rb") as f:
    PRIVATE = f.read()
with open(settings.public_key_path, "rb") as f:
    PUBLIC = f.read()

def now() -> int: return int(time.time())

def create_access(sub: str) -> str:
    return jwt.encode(
        {"sub": sub, "typ": "access", "iat": now(), "exp": now()+settings.access_exp_minutes*60, "jti": str(uuid.uuid4())},
        PRIVATE, algorithm=settings.jwt_alg
    )

def create_refresh(sub: str, jti: str) -> str:
    return jwt.encode(
        {"sub": sub, "typ": "refresh", "iat": now(), "exp": now()+settings.refresh_exp_days*24*3600, "jti": jti},
        PRIVATE, algorithm=settings.jwt_alg
    )

def decode_token(token: str) -> dict:
    return jwt.decode(token, PUBLIC, algorithms=[settings.jwt_alg])

def is_refresh(payload: dict) -> bool:
    return payload.get("typ") == "refresh"
EOF

# -------- app/core/redis_client.py --------
cat > app/core/redis_client.py <<'EOF'
import aioredis
from .config import settings
redis = aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
EOF

# -------- app/core/emailer.py --------
cat > app/core/emailer.py <<'EOF'
import aiosmtplib
from email.message import EmailMessage
from .config import settings

async def send_email(to: str, subject: str, html: str) -> None:
    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content("HTML email only")
    msg.add_alternative(html, subtype="html")
    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        start_tls=True,
        username=settings.smtp_user,
        password=settings.smtp_pass,
    )
EOF

# -------- app/core/security_utils.py --------
cat > app/core/security_utils.py <<'EOF'
import time, hashlib
from fastapi import HTTPException, Request
from .redis_client import redis

def fingerprint_from_request(request: Request) -> str:
    ua = request.headers.get("user-agent", "")
    ip = request.client.host if request.client else ""
    return hashlib.sha256(f"{ua}|{ip}".encode()).hexdigest()

async def rate_limit_or_429(key: str, limit: int, window_sec: int):
    now = int(time.time())
    window_key = f"{key}:{now // window_sec}"
    cur = await redis.incr(window_key)
    if cur == 1: await redis.expire(window_key, window_sec)
    if cur > limit: raise HTTPException(429, "Too many requests, try later")

async def track_login_fail(email: str, ttl_sec: int = 900, max_fails: int = 5) -> bool:
    key = f"login:fail:{email.lower()}"
    fails = await redis.incr(key)
    if fails == 1: await redis.expire(key, ttl_sec)
    return fails >= max_fails

async def reset_login_fail(email: str):
    await redis.delete(f"login:fail:{email.lower()}")
EOF

# -------- app/core/token_store.py --------
cat > app/core/token_store.py <<'EOF'
import time, secrets, hashlib
from ..db import email_tokens, reset_tokens

def _gen() -> str: return secrets.token_urlsafe(32)
def _h(v: str) -> str: return hashlib.sha256(v.encode()).hexdigest()

async def create_email_verify_token(user_id: str, email: str, ttl_minutes: int = 60) -> str:
    raw = _gen()
    await email_tokens.insert_one({"user_id": user_id, "email": email, "h": _h(raw), "exp": int(time.time())+ttl_minutes*60, "used": False, "kind":"verify"})
    return raw

async def verify_email_token(raw: str):
    h = _h(raw)
    doc = await email_tokens.find_one({"h": h, "kind":"verify", "used": False})
    if not doc or doc["exp"] < int(time.time()): return None
    await email_tokens.update_one({"_id": doc["_id"]}, {"$set":{"used": True}})
    return doc

async def create_reset_token(user_id: str, email: str, ttl_minutes: int = 30) -> str:
    raw = _gen()
    await reset_tokens.insert_one({"user_id": user_id, "email": email, "h": _h(raw), "exp": int(time.time())+ttl_minutes*60, "used": False, "kind":"reset"})
    return raw

async def use_reset_token(raw: str):
    h = _h(raw)
    doc = await reset_tokens.find_one({"h": h, "kind":"reset", "used": False})
    if not doc or doc["exp"] < int(time.time()): return None
    await reset_tokens.update_one({"_id": doc["_id"]}, {"$set":{"used": True}})
    return doc
EOF

# -------- app/db.py --------
cat > app/db.py <<'EOF'
from motor.motor_asyncio import AsyncIOMotorClient
from .core.config import settings

_client = AsyncIOMotorClient(settings.mongo_url)
db = _client.get_default_database() or _client["proplus"]

users = db["users"]
refresh_tokens = db["refresh_tokens"]
auth_events = db["auth_events"]
email_tokens = db["email_tokens"]
reset_tokens = db["reset_tokens"]
EOF

# -------- app/schemas.py --------
cat > app/schemas.py <<'EOF'
from pydantic import BaseModel, EmailStr, Field

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class MeOut(BaseModel):
    id: str
    email: EmailStr
EOF

# -------- app/models.py (bcrypt + >72 fix) --------
cat > app/models.py <<'EOF'
import hashlib, time
from passlib.context import CryptContext
from bson import ObjectId
from .db import users

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _normalize_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest() if len(pw) > 72 else pw

def hash_password(pw: str) -> str:
    return pwd_ctx.hash(_normalize_pw(pw))

def verify_password(pw: str, hashed: str) -> bool:
    return pwd_ctx.verify(_normalize_pw(pw), hashed)

async def create_user(email: str, password: str) -> str:
    if await users.find_one({"email": email}): return ""
    res = await users.insert_one({"email": email, "password_hash": hash_password(password), "email_verified": False, "locked_until": 0, "created_at": int(time.time())})
    return str(res.inserted_id)

async def get_user_by_email(email: str): return await users.find_one({"email": email})
async def get_user_by_id(uid: str): return await users.find_one({"_id": ObjectId(uid)})
EOF

# -------- app/auth_v2.py --------
cat > app/auth_v2.py <<'EOF'
import time, uuid, hashlib
from fastapi import APIRouter, HTTPException, Header, Body, Request, status
from pydantic import EmailStr, Field
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
async def refresh_token(refresh_token: str = Body(..., embed=True), request: Request | None = None):
    payload = decode_token(refresh_token)
    if not is_refresh(payload): raise HTTPException(400, "not a refresh token")
    h = jti_hash(payload["jti"])
    doc = await refresh_tokens.find_one({"jti_hash": h, "revoked": False})
    if not doc: raise HTTPException(401, "refresh invalid or revoked")
    await refresh_tokens.update_one({"_id": doc["_id"]}, {"$set":{"revoked": True, "revoked_at": int(time.time())}})
    sub = payload["sub"]; new_jti = str(uuid.uuid4())
    new_refresh = create_refresh(sub, new_jti)
    await refresh_tokens.insert_one({"user_id": ObjectId(sub), "jti_hash": jti_hash(new_jti), "issued_at": int(time.time()), "expires_at": int(time.time())+30*24*3600, "fp": fingerprint_from_request(request) if request else None, "revoked": False})
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
EOF

# -------- app/main.py --------
cat > app/main.py <<'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .auth_v2 import router as auth_router

app = FastAPI(title="ProPlus API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourprod.domain"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/healthz")
async def healthz(): return {"ok": True}
app.include_router(auth_router, prefix="/auth", tags=["auth"])
EOF

# -------- scripts/smoke_auth.sh --------
mkdir -p app/scripts
cat > app/scripts/smoke_auth.sh <<'EOF'
#!/usr/bin/env bash
set -e
API=${API:-http://localhost:8000}

echo "[1] health"; curl -s ${API}/healthz; echo
echo "[2] register"; curl -s -X POST ${API}/auth/register -H "Content-Type: application/json" -d '{"email":"a@a.com","password":"Password12345"}'; echo
echo "[3] login"; LOGIN=$(curl -s -X POST ${API}/auth/login -H "Content-Type: application/json" -d '{"email":"a@a.com","password":"Password12345"}'); echo $LOGIN
AT=$(echo $LOGIN | python - <<'PY'
import sys,json; print(json.load(sys.stdin)["access_token"])
PY
)
RT=$(echo $LOGIN | python - <<'PY'
import sys,json; print(json.load(sys.stdin)["refresh_token"])
PY
)
echo "[4] me"; curl -s ${API}/auth/me -H "Authorization: Bearer ${AT}"; echo
echo "[5] refresh"; curl -s -X POST ${API}/auth/refresh -H "Content-Type: application/json" -d "{\"refresh_token\":\"${RT}\"}"; echo
EOF
chmod +x app/scripts/smoke_auth.sh

# -------- RSA keys (dev only) --------
if [ ! -f secrets/jwt_private.pem ]; then
  openssl genrsa -out secrets/jwt_private.pem 2048
  openssl rsa -in secrets/jwt_private.pem -pubout -out secrets/jwt_public.pem
fi

echo "Done. Copy .env.example to .env and fill values."
