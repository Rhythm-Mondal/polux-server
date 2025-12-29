from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.logic.space import (
    get_user_space_by_name,
    create_user_space,
    list_user_spaces,
    count_listed_user_spaces,
    rename_user_space,
    delete_user_space,
)
from app.schemas.common import Token
from app.schemas.space import (
    CreateSpace,
    ListSpacesResponse,
    ListSpaces,
    DeleteSpace,
    RenameSpace,
)
from app.utils import database
from app.utils.auth import get_auth_user

router = APIRouter(
    prefix="/spaces",
)


@router.post("")
def create_space(
    body: CreateSpace,
    user: Token = Depends(get_auth_user),
    db: Session = Depends(database.get_session),
):
    if get_user_space_by_name(db, user.user_id, body.name) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Space with the same name already exists",
        )

    if not create_user_space(db, user, body):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create space"
        )
    return {"message": "Space created successfully"}


@router.get("", response_model=ListSpacesResponse)
def list_spaces(
    query: ListSpaces = Depends(),
    user: Token = Depends(get_auth_user),
    db: Session = Depends(database.get_session),
):
    spaces = list_user_spaces(db, user.user_id, query.offset, query.limit)
    total = count_listed_user_spaces(db, user.user_id)
    return {"spaces": spaces, "total": total}


@router.patch("/{space_id}")
def rename_space(
    space_id: UUID,
    body: RenameSpace,
    user: Token = Depends(get_auth_user),
    db: Session = Depends(database.get_session),
):
    result = rename_user_space(db, user.user_id, space_id, body.name)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to rename space"
        )
    return {"message": "Space renamed successfully"}


@router.delete("/{space_id}")
def delete_space(
    space_id: UUID,
    query: DeleteSpace = Depends(),
    user: Token = Depends(get_auth_user),
    db: Session = Depends(database.get_session),
):
    result = delete_user_space(db, user.user_id, space_id, query.delete_contents)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete space"
        )
    return {"message": "Space deleted successfully"}
