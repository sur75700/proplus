from fastapi import Depends, HTTPException, Header
from jose import JWTError
from ..core.jwt_utils import decode_token
from ..models import get_user_by_id

async def admin_required(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "No bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(401, "Invalid token")
    uid = payload.get("sub")
    user = await get_user_by_id(uid)
    if not user:
        raise HTTPException(401, "User not found")
    if user.get("role") != "admin":
        raise HTTPException(403, "Admin only")
    return user
