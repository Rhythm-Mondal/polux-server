from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.logic.space import logic_get_user_default_space
from app.schemas.session import UserLogin
from app.logic.user import logic_get_user_by_email
from app.utils.auth import verify_password, create_access_token
from app.utils import database

router = APIRouter()


@router.post("/login")
def login(body: UserLogin, db: Session = Depends(database.get_session)):
    db_user = logic_get_user_by_email(db, email=str(body.email))
    if not db_user or not verify_password(
        body.password.get_secret_value(), db_user.password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )

    db_space = logic_get_user_default_space(db, db_user.id)

    token = create_access_token(
        {
            "user_id": str(db_user.id),
            "email": str(db_user.email),
            "space_id": str(db_space.id),
        }
    )
    return {"access_token": token}
