import logging
from typing import Literal
from uuid import UUID

from fastapi import Path, HTTPException, status, Depends
from sqlalchemy import update, or_, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.node import Space, Node
from app.schemas.common import Token
from app.schemas.space import CreateSpace
from app.utils.auth import get_auth_user


def logic_resolve_default_space_id(
    user: Token = Depends(get_auth_user), space_id: UUID | Literal["me"] = Path()
):
    if isinstance(space_id, UUID):
        return space_id

    if not user.space_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Space not found"
        )

    return user.space_id


def logic_create_user_default_space(db: Session, user_id: UUID) -> Space | None:
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


def logic_get_user_default_space(db: Session, user_id: UUID) -> Space:
    return db.query(Space).filter(Space.owner_id == user_id).first()


def logic_create_space(db: Session, user: Token, body: CreateSpace) -> Space | None:
    try:
        space = Space(
            name=body.name,
            owner_id=user.user_id,
        )
        db.add(space)
        db.commit()
        return space
    except Exception as e:
        db.rollback()
        logging.error(e)
        return None


def logic_get_user_space_by_name(db: Session, user_id: UUID, name: str) -> Space | None:
    return (
        db.query(Space)
        .filter(and_(Space.name == name, Space.owner_id == user_id))
        .first()
    )


def logic_list_spaces(db: Session, user_id: UUID, offset: int = None, limit: int = None):
    query = db.query(Space).filter(Space.owner_id == user_id).order_by(Space.created_at)
    if offset is not None:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def logic_count_listed_spaces(db: Session, user_id: UUID):
    return db.query(Space).filter(Space.owner_id == user_id).count()


def logic_rename_space(db: Session, user_id: UUID, space_id: UUID, name: str):
    space = (
        db.query(Space)
        .filter(and_(Space.owner_id == user_id, Space.id == space_id))
        .first()
    )
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Space not found"
        )

    try:
        space.name = name
        db.commit()
        return space
    except IntegrityError as e:
        logging.error(e)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Space with same name already exists",
        )


def logic_delete_space(
    db: Session, user_id: UUID, space_id: UUID, delete_contents: bool = False
):
    space = (
        db.query(Space)
        .filter(and_(Space.owner_id == user_id, Space.id == space_id))
        .first()
    )
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Space not found"
        )

    if space.is_default:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete default space"
        )

    total_space_nodes = db.query(Node).filter(Node.space_id == space_id).count()
    if total_space_nodes > 0 and not delete_contents:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Space contains files/folders do you wish delete those as well?",
        )

    try:
        db.delete(space)
        db.commit()
        return space
    except Exception as e:
        logging.error(e)
        db.rollback()
        raise None
