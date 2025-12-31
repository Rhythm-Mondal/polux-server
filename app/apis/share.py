from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.logic.share import logic_list_shared_nodes, logic_count_listed_shared_nodes
from app.logic.space import logic_resolve_default_space_id
from app.schemas.common import Token
from app.schemas.share import (
    ListSharedNodesResponse,
    ShareNode,
    ListSharesResponse,
    ListSharedNodes,
    ListShares,
)
from app.utils import database
from app.utils.auth import get_auth_user

router = APIRouter(prefix="/spaces")


@router.put("/me/nodes/{node_id}")
@router.put("/{space_id}/nodes/{node_id}")
def share_node(
    node_id: int,
    body: ShareNode,
    space_id: UUID = Depends(logic_resolve_default_space_id),
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


@router.get("/shares/list", response_model=ListSharedNodesResponse)
def list_shared_nodes(
    query: ListSharedNodes = Depends(),
    user: Token = Depends(get_auth_user),
    db: Session = Depends(database.get_session),
):
    nodes = logic_list_shared_nodes(db, user.user_id, query)
    total = logic_count_listed_shared_nodes(db, user.user_id)
    return {"nodes": nodes, "total": total}
