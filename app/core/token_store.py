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
