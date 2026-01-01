from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.logic.archive import (
    logic_restore_node,
    logic_list_archive,
    logic_count_listed_archive,
)
from app.logic.space import logic_resolve_default_space_id
from app.schemas.archive import ListArchiveResponse, ListArchive, RestoreNode
from app.schemas.common import Token
from app.utils import database
from app.utils.auth import get_auth_user

router = APIRouter(
    prefix="/spaces",
)


@router.get("/me/archives", response_model=ListArchiveResponse)
@router.get("/{space_id}/archives", response_model=ListArchiveResponse)
def list_archive(
    query: ListArchive = Depends(),
    space_id: UUID = Depends(logic_resolve_default_space_id),
    user: Token = Depends(get_auth_user),
    db: Session = Depends(database.get_session),
):
    nodes = logic_list_archive(db, user.user_id, space_id, query)
    total = logic_count_listed_archive(db, space_id, query)
    return {"nodes": nodes, "total": total}


@router.patch("/me/nodes/{node_id}/restore")
@router.patch("/{space_id}/nodes/{node_id}/restore")
def restore_node(
    node_id: int,
    body: RestoreNode,
    space_id: UUID = Depends(logic_resolve_default_space_id),
    user: Token = Depends(get_auth_user),
    db: Session = Depends(database.get_session),
):
    result = logic_restore_node(db, user.user_id, space_id, node_id, body)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to restore node"
        )
    return {"message": "Successfully restored node"}
