import logging

from sqlalchemy.orm import Session
from app import models, schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def get_user_by_email(db: Session, email: str) -> models.user.User:
    return db.query(models.user.User).filter(models.user.User.email == email).first()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_user(db: Session, user: schemas.user.UserCreate) -> models.user.User | None:
    hashed_password = pwd_context.hash(user.password.get_secret_value())
    try:
        db_user = models.user.User(
            name=user.name, email=user.email, password=hashed_password
        )
        db.add(db_user)
        db.commit()
        return db_user
    except Exception as e:
        logging.error(e)
        db.rollback()
        return None
