import os
from datetime import datetime, timedelta, UTC

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from passlib.context import CryptContext

from app.schemas.common import Token

SECRET_KEY = os.getenv("SECRET_KEY")
TOKEN_EXPIRE_MINUTES = os.getenv("TOKEN_EXPIRE_MINUTES")

security = HTTPBearer()
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()
    if TOKEN_EXPIRE_MINUTES:
        to_encode.update(
            {
                "exp": (
                    datetime.now(UTC) + timedelta(minutes=int(TOKEN_EXPIRE_MINUTES))
                ).timestamp()
            }
        )

    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")


def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = Token(**payload)

        if user.exp and user.exp < datetime.now(UTC).timestamp():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
            )

        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not verify credentials",
        ) from e


def get_auth_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        token = credentials.credentials
        return verify_access_token(token)
    except Exception as e:
        raise e
