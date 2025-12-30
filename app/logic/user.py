import logging

from sqlalchemy import or_, any_
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.auth import hash_password


def logic_create_user(db: Session, user: UserCreate) -> User | None:
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


def logic_get_user_by_email(db: Session, email: str) -> User:
    return db.query(User).filter(User.email == email).first()


def logic_search_users(
    db: Session, search_tokens: list[str], offset: int = 0, limit: int = 10
):
    query = db.query(User)
    if search_tokens:
        patterns = [t + "%" for t in search_tokens]
        query = query.filter(
            or_(
                User.name.ilike(any_(patterns)),
                User.email.ilike(any_(patterns)),
            )
        )
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def logic_count_searched_users(db: Session, search_tokens: list[str]):
    query = db.query(User)
    if search_tokens:
        patterns = [t + "%" for t in search_tokens]
        query = query.filter(
            or_(
                User.name.ilike(any_(patterns)),
                User.email.ilike(any_(patterns)),
            )
        )
    return query.count()
