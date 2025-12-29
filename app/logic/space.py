import logging
from uuid import UUID

from fastapi import Path, Header, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.models.node import Space
from app.schemas.common import Token
from app.utils.auth import get_auth_user


def resolve_default_space_id(
    user: Token = Depends(get_auth_user), space_id: UUID | None = Path()
):
    if space_id is not None:
        return space_id

    space_id = user.space_id
    if not space_id:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Space not found"
        )

    return space_id


def create_user_default_space(db: Session, user_id: UUID) -> Space | None:
    try:
        db_space = Space(
            name="Your Space",
            owner_id=user_id,
            is_default=True,
        )
        db.add(db_space)
        db.commit()
        return db_space
    except Exception as e:
        db.rollback()
        logging.error(e)
        return None


def get_user_default_space(db: Session, user_id: UUID) -> Space:
    return db.query(Space).filter(Space.owner_id == user_id).first()
