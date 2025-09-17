from fastapi import APIRouter, HTTPException
from models import UserCreate, UserOut, LoginIn
from utils import hash_password, verify_password, make_jwt
from db import db

router = APIRouter()


@router.post("/register", response_model=UserOut)
async def register(user: UserCreate):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(400, "User already exists")
    doc = {"email": user.email, "password": hash_password(user.password)}
    res = await db.users.insert_one(doc)
    return {"_id": str(res.inserted_id), "email": user.email}


@router.post("/login")
async def login(data: LoginIn):
    user = await db.users.find_one({"email": data.email})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(401, "Invalid credentials")
    token = make_jwt(str(user["_id"]))
    return {"access_token": token, "token_type": "bearer"}
