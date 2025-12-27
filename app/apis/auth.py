from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from app.schemas.user import UserCreate, UserLogin
from app.logic.user import get_user_by_email, create_user
from app.utils.auth import verify_password
from app.utils import database, auth

router = APIRouter()


@router.post("/register")
def register(user: UserCreate, db: Session = Depends(database.get_db)):
    if get_user_by_email(db, email=str(user.email)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    if not create_user(db, user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to register user"
        )
    return {"message": "User registered"}


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(database.get_db)):
    db_user = get_user_by_email(db, email=str(user.email))
    if not db_user or not verify_password(
        user.password.get_secret_value(), db_user.password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )

    token = auth.create_access_token(
        {"user_id": str(db_user.id), "email": db_user.email, "name": db_user.name}
    )
    return {"access_token": token}
