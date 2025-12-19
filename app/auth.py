import os
from datetime import datetime, timedelta, UTC
from jose import jwt

SECRET_KEY = os.getenv("SECRET_KEY")
TOKEN_EXPIRE_MINUTES = os.getenv("TOKEN_EXPIRE_MINUTES")


def create_access_token(data: dict):
    to_encode = data.copy()
    if TOKEN_EXPIRE_MINUTES:
        to_encode.update({"exp": datetime.now(UTC) + timedelta(minutes=int(TOKEN_EXPIRE_MINUTES))})

    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")