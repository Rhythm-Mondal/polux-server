from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.share import (
    ListSharedNodesResponse,
    ShareNode,
    ListSharesResponse,
    ListSharedNodes,
    ListShares,
)
from app.utils import database

router = APIRouter(prefix="/shares")


@router.put("/me/nodes/{node_id}")
def share_node_default(
    node_id: int, body: ShareNode, db: Session = Depends(database.get_db)
):
    pass


@router.put("/{space_id}/nodes/{node_id}")
def share_node(space_id: UUID, node_id: int, body: ShareNode):
    pass


@router.get("/me/nodes/{node_id}/shares", response_model=ListSharesResponse)
def list_shared_with_users_default(
    node_id: int, query: ListShares, db: Session = Depends(database.get_db)
):
    pass


@router.get("/{space_id}/nodes/{node_id}/shares", response_model=ListSharesResponse)
def list_shared_with_users(
    space_id: UUID,
    node_id: int,
    query: ListShares,
    db: Session = Depends(database.get_db),
):
    pass


@router.get("/shared/nodes", response_model=ListSharedNodesResponse)
def list_shared_nodes(query: ListSharedNodes, db: Session = Depends(database.get_db)):
    pass
