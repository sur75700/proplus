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
    res = await users.insert_one({"email": email, "password_hash": hash_password(password), "email_verified": False,
        "role": "user", "locked_until": 0, "created_at": int(time.time())})
    return str(res.inserted_id)

async def get_user_by_email(email: str): return await users.find_one({"email": email})
async def get_user_by_id(uid: str): return await users.find_one({"_id": ObjectId(uid)})
