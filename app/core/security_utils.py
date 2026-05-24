import hashlib
import time

from fastapi import HTTPException, Request

from .redis_client import redis


def fingerprint_from_request(req: Request) -> str:
    ua = req.headers.get("user-agent", "")
    ip = req.client.host if req.client else ""
    return hashlib.sha256(f"{ip}|{ua}".encode()).hexdigest()


async def rate_limit(key: str, limit: int, window_sec: int):
    now = int(time.time())
    window_key = f"{key}:{now // window_sec}"
    cur = await redis.incr(window_key)

    if cur == 1:
        await redis.expire(window_key, window_sec)

    if cur > limit:
        raise HTTPException(429, "Too many requests, try later")


async def rate_limit_or_429(key: str, limit: int, window_sec: int):
    await rate_limit(key, limit, window_sec)


async def track_login_fail(email: str, ttl_sec: int = 900, max_fails: int = 5) -> bool:
    key = f"login:fail:{email.lower()}"
    fails = await redis.incr(key)

    if fails == 1:
        await redis.expire(key, ttl_sec)

    return fails >= max_fails


async def clear_login_fail(email: str):
    await redis.delete(f"login:fail:{email.lower()}")


async def reset_login_fail(email: str):
    await clear_login_fail(email)
