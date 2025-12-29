from uuid import UUID

from fastapi import Path, Header, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.models.node import Space
from app.schemas.common import Token
from app.utils.auth import get_auth_user


def resolve_default_space_id(user: Token = Depends(get_auth_user), space_id: UUID | None = Path(None)):
    if space_id is not None:
        return space_id

    space_id = user.space_id
    if not space_id:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Space not found")

    return space_id


def get_user_default_space(db: Session, user_id: UUID) -> Space:
    return db.query(Space).filter(Space.owner_id == user_id).first()