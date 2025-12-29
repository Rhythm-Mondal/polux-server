from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.logic.space import create_user_default_space
from app.logic.user import (
    get_user_by_email,
    create_user,
    search_user,
    count_searched_users,
)
from app.schemas.common import Token
from app.schemas.user import UserCreate, UserSearch, UserSearchResponse
from app.utils import database
from app.utils.auth import get_auth_user

router = APIRouter()


@router.post("/register")
def register(body: UserCreate, db: Session = Depends(database.get_session)):
    if get_user_by_email(db, email=str(body.email)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    db_user = create_user(db, body)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to register user"
        )
    if not create_user_default_space(db, db_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create default space",
        )
    return {"message": "User registered"}


@router.post("/users/search", response_model=UserSearchResponse)
def search_users(
    body: UserSearch,
    user: Token = Depends(get_auth_user),
    db: Session = Depends(database.get_session),
):
    users = search_user(db, body.search_tokens, body.offset, body.limit)
    total = count_searched_users(db, body.search_tokens)
    return {"users": users, "total": total}
