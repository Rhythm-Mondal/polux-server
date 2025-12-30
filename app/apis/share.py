from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.logic.space import logic_resolve_default_space_id
from app.schemas.share import (
    ListSharedNodesResponse,
    ShareNode,
    ListSharesResponse,
    ListSharedNodes,
    ListShares,
)
from app.utils import database

router = APIRouter(prefix="/spaces")


@router.put("/me/nodes/{node_id}")
@router.put("/{space_id}/nodes/{node_id}")
def share_node(
    node_id: int, body: ShareNode, space_id: UUID = Depends(logic_resolve_default_space_id)
):
    pass


@router.get("/me/nodes/{node_id}/shares", response_model=ListSharesResponse)
@router.get("/{space_id}/nodes/{node_id}/shares", response_model=ListSharesResponse)
def list_shared_with_users(
    node_id: int,
    space_id: UUID = Depends(logic_resolve_default_space_id),
    query: ListShares = Depends(),
    db: Session = Depends(database.get_session),
):
    pass


@router.get("/shared/nodes", response_model=ListSharedNodesResponse)
def list_shared_nodes(
    query: ListSharedNodes = Depends(), db: Session = Depends(database.get_session)
):
    pass
