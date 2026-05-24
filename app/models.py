import hashlib
import time

from bson import ObjectId
from passlib.context import CryptContext

from .db import users

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(p: str) -> str:
    return pwd.hash(p)


def verify_password(p: str, h: str) -> bool:
    return pwd.verify(p, h)


def user_public(u):
    return {"id": str(u["_id"]), "email": u["email"]}


async def create_user(email: str, password: str) -> str:
    if await users.find_one({"email": email}):
        return ""

    res = await users.insert_one(
        {
            "email": email,
            "password_hash": hash_password(password),
            "email_verified": False,
            "role": "user",
            "locked_until": 0,
            "created_at": int(time.time()),
        }
    )
    return str(res.inserted_id)


async def get_user_by_email(email: str):
    return await users.find_one({"email": email})


async def get_user(uid: str):
    return await users.find_one({"_id": ObjectId(uid)})


def jti_hash(jti: str) -> str:
    return hashlib.sha256(jti.encode()).hexdigest()
