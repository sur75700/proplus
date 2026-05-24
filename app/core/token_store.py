import hashlib
import secrets
import time

from ..db import email_tokens, reset_tokens


def _h(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


async def create_email_token(user_id, kind: str = "verify", ttl_sec: int = 3600) -> str:
    raw = secrets.token_urlsafe(32)
    await email_tokens.insert_one(
        {
            "user_id": user_id,
            "kind": kind,
            "h": _h(raw),
            "exp": int(time.time()) + ttl_sec,
            "used": False,
        }
    )
    return raw


async def consume_email_token(raw: str):
    h = _h(raw)
    doc = await email_tokens.find_one({"h": h, "kind": "verify", "used": False})

    if not doc or doc["exp"] < int(time.time()):
        return None

    await email_tokens.update_one({"_id": doc["_id"]}, {"$set": {"used": True}})
    return doc


async def create_reset_token(user_id, ttl_sec: int = 1800) -> str:
    raw = secrets.token_urlsafe(32)
    await reset_tokens.insert_one(
        {
            "user_id": user_id,
            "kind": "reset",
            "h": _h(raw),
            "exp": int(time.time()) + ttl_sec,
            "used": False,
        }
    )
    return raw


async def consume_reset_token(raw: str):
    h = _h(raw)
    doc = await reset_tokens.find_one({"h": h, "kind": "reset", "used": False})

    if not doc or doc["exp"] < int(time.time()):
        return None

    await reset_tokens.update_one({"_id": doc["_id"]}, {"$set": {"used": True}})
    return doc
