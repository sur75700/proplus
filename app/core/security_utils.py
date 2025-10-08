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
