# auth.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from bson import ObjectId
import jwt

import db as dbmod
from utils import hash_password, verify_password, make_jwt
from settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


# --------- Pydantic Schemas ---------
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


# --------- Helpers ---------
async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
):
    token = creds.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    uid = payload.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    if dbmod.db is None:
        raise HTTPException(status_code=503, detail="DB not ready")

    user = await dbmod.db.users.find_one({"_id": ObjectId(uid)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"_id": str(user["_id"]), "email": user["email"]}


# --------- Routes ---------
@router.post("/register")
async def register(user: UserCreate):
    if dbmod.db is None:
        raise HTTPException(status_code=503, detail="DB not ready")

    existing = await dbmod.db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    doc = {
        "email": user.email,
        "password": hash_password(user.password),
    }
    res = await dbmod.db.users.insert_one(doc)
    return {"_id": str(res.inserted_id), "email": user.email}


@router.post("/login")
async def login(data: LoginIn):
    if dbmod.db is None:
        raise HTTPException(status_code=503, detail="DB not ready")

    user = await dbmod.db.users.find_one({"email": data.email})
    if not user or not verify_password(data.password, user["password"]):
        # Կանոնավոր սխալ՝ ոչ թե 500
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = make_jwt(str(user["_id"]))
    # Վերադարձնում ենք մաքուր JSON մեկ օբյեկտով
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
async def me(current=Depends(get_current_user)):
    return current
