from bson import ObjectId
from fastapi import Header, HTTPException, status
from jose import JWTError

from ..db import users
from .jwt_utils import decode_token


def _extract_bearer(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No bearer token",
        )
    return authorization.split(" ", 1)[1]


def _decode_or_401(token: str) -> dict:
    try:
        return decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token",
        )


async def admin_required(authorization: str = Header(None)) -> dict:
    payload = _decode_or_401(_extract_bearer(authorization))

    if payload.get("typ") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="access token required",
        )

    uid = payload.get("sub")
    if not uid or not ObjectId.is_valid(uid):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token subject",
        )

    user = await users.find_one({"_id": ObjectId(uid)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid token user",
        )

    if user.get("role", "user") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="admin required",
        )

    return user
