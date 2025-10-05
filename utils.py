from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import jwt

from settings import settings

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd.verify(password, hashed)


def make_jwt(sub: str) -> str:
    exp = datetime.now(tz=timezone.utc) + timedelta(minutes=settings.JWT_EXPIRES_MIN)
    payload = {"sub": sub, "exp": exp}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
