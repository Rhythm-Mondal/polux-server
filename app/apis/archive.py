from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.archive import ListArchiveResponse, ListArchive, RestoreNode
from app.schemas.share import ListSharedNodesResponse
from app.utils import database

router = APIRouter(
    prefix="/spaces",
)


@router.get("/me/archives", response_model=ListArchiveResponse)
def list_archives_default(query: ListArchive, db: Session = Depends(database.get_db)):
    pass


@router.get("/{space_id}/archives", response_model=ListArchiveResponse)
def list_archive(
    space_id: UUID, query: ListArchive, db: Session = Depends(database.get_db)
):
    pass


@router.patch("/me/nodes/{node_id}/restore")
def restore_node_default(
    node_id: int, body: RestoreNode, db: Session = Depends(database.get_db)
):
    pass


@router.patch("/{space_id}/nodes/{node_id}/restore")
def restore_node(
    space_id: UUID,
    node_id: int,
    body: RestoreNode,
    db: Session = Depends(database.get_db),
):
    pass
