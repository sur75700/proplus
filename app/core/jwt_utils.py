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
