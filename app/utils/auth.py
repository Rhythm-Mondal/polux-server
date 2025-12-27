import os
from datetime import datetime, timedelta, UTC
from jose import jwt
from passlib.context import CryptContext

SECRET_KEY = os.getenv("SECRET_KEY")
TOKEN_EXPIRE_MINUTES = os.getenv("TOKEN_EXPIRE_MINUTES")

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()
    if TOKEN_EXPIRE_MINUTES:
        to_encode.update(
            {"exp": datetime.now(UTC) + timedelta(minutes=int(TOKEN_EXPIRE_MINUTES))}
        )

    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
