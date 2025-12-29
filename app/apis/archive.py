from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.logic.space import resolve_default_space_id
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
    query: ListArchive,
    space_id: UUID = Depends(resolve_default_space_id),
    user: Token = Depends(get_auth_user),
    db: Session = Depends(database.get_session),
):
    pass


@router.patch("/me/nodes/{node_id}/restore")
@router.patch("/{space_id}/nodes/{node_id}/restore")
def restore_node(
    node_id: int,
    body: RestoreNode,
    space_id: UUID = Depends(resolve_default_space_id),
    user: Token = Depends(get_auth_user),
    db: Session = Depends(database.get_session),
):
    pass
