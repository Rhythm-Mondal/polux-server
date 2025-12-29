from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.logic.user import get_user_by_email, create_user
from app.schemas.user import UserCreate, UserSearch, UserSearchResponse
from app.utils import database

router = APIRouter()


@router.post("/register")
def register(body: UserCreate, db: Session = Depends(database.get_session)):
    if get_user_by_email(db, email=str(body.email)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    if not create_user(db, body):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to register user"
        )
    return {"message": "User registered"}


@router.post("/users/search", response_model=UserSearchResponse)
def search_users(body: UserSearch, db: Session = Depends(database.get_session)):
    pass
