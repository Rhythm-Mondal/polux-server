from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.utils import database
from app.schemas.archive import ListArchiveResponse, ListArchive, RestoreNode
from app.logic.node import get_default_space_id

router = APIRouter(
    prefix="/spaces",
)

@router.get("/me/archives", response_model=ListArchiveResponse)
@router.get("/{space_id}/archives", response_model=ListArchiveResponse)
def list_archive(
    space_id: UUID = Depends(get_default_space_id), query: ListArchive = Depends(),  db: Session = Depends(database.get_db)
):
    pass


@router.patch("/me/nodes/{node_id}/restore")
@router.patch("/{space_id}/nodes/{node_id}/restore")
def restore_node(
    space_id: UUID = Depends(get_default_space_id),
    node_id: int = Depends(),
    body: RestoreNode = Depends(),
    db: Session = Depends(database.get_db),
):
    pass
