import logging

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.auth import hash_password


def get_user_by_email(db: Session, email: str) -> User:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate) -> User | None:
    hashed_password = hash_password(user.password.get_secret_value())
    try:
        db_user = User(name=user.name, email=user.email, password=hashed_password)
        db.add(db_user)
        db.commit()
        return db_user
    except Exception as e:
        logging.error(e)
        db.rollback()
        return None
