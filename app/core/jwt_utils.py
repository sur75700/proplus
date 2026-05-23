import time
import uuid
from pathlib import Path

from jose import jwt

from .config import settings


def _read_key(configured_path: str, local_fallback: str, label: str) -> bytes:
    candidates = [
        Path(configured_path),
        Path(local_fallback),
    ]

    for path in candidates:
        if path.exists():
            return path.read_bytes()

    checked = ", ".join(str(p) for p in candidates)
    raise RuntimeError(
        f"{label} key not found. Checked: {checked}. "
        "Generate local keys in ./secrets or mount Docker secrets."
    )


PRIVATE = _read_key(
    settings.private_key_path,
    "secrets/jwt_private.pem",
    "JWT private",
)

PUBLIC = _read_key(
    settings.public_key_path,
    "secrets/jwt_public.pem",
    "JWT public",
)


def now() -> int:
    return int(time.time())


def create_access(sub: str) -> str:
    return jwt.encode(
        {
            "sub": sub,
            "typ": "access",
            "iat": now(),
            "exp": now() + settings.access_exp_minutes * 60,
            "jti": str(uuid.uuid4()),
        },
        PRIVATE,
        algorithm=settings.jwt_alg,
    )


def create_refresh(sub: str, jti: str) -> str:
    return jwt.encode(
        {
            "sub": sub,
            "typ": "refresh",
            "iat": now(),
            "exp": now() + settings.refresh_exp_days * 24 * 3600,
            "jti": jti,
        },
        PRIVATE,
        algorithm=settings.jwt_alg,
    )


def decode_token(token: str) -> dict:
    return jwt.decode(token, PUBLIC, algorithms=[settings.jwt_alg])


def is_refresh(payload: dict) -> bool:
    return payload.get("typ") == "refresh"
