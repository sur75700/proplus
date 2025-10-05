from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ---- Auth ----
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: EmailStr


class LoginIn(BaseModel):
    email: EmailStr
    password: str


# ---- Projects ----
class ProjectIn(BaseModel):
    title: str
    description: Optional[str] = None


class ProjectOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    owner_id: str
    created_at: datetime
