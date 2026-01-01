from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, select, func
from sqlalchemy.orm import Session
from sqlalchemy_utils import Ltree
from starlette import status

from app.models.node import Node, NodeStatus, NodeType
from app.models.share import NodeShare, SpaceShare, SharePermission
from app.models.space import Space


def logic_node_to_output_dict(node: Node):
    return {
        "id": node.id,
        "space_id": node.space_id,
        "parent_id": node.parent_id,
        "name": node.name,
        "type": node.type,
        "uploader_id": node.uploader_id,
        "created_at": node.created_at,
        "updated_at": node.updated_at,
    }


def logic_node_can_general(node: Node, permission: int, is_owner: bool):
    return {
        "open": permission >= SharePermission.READ,
        "upload": node.type == NodeType.FOLDER and permission >= SharePermission.WRITE,
        "download": node.type == NodeType.FILE and permission >= SharePermission.READ,
        "rename": permission >= SharePermission.WRITE,
        "copy": permission >= SharePermission.READ,
        "cut": permission >= SharePermission.WRITE,
        "paste": node.type == NodeType.FOLDER and permission >= SharePermission.WRITE,
        "archive": permission >= SharePermission.WRITE,
        "delete": is_owner,
        "share": permission >= SharePermission.MANAGE,
    }


def logic_node_can_archive(node: Node, permission: int, is_owner: bool):
    return {"restore": permission >= SharePermission.MANAGE, "delete": is_owner}


def logic_get_space_and_node(
    db: Session, space_id: UUID, node_id: int = None
) -> tuple[Space, Node | None]:
    db_space = db.query(Space).filter(Space.id == space_id).first()
    if not db_space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Space not found"
        )

    db_node = (
        db.query(Node)
        .filter(
            and_(
                Node.space_id == space_id,
                Node.id == node_id,
                Node.status != NodeStatus.DELETED,
            )
        )
        .first()
    )
    if node_id is not None and not db_node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Space not found"
        )

    return db_space, db_node


def node_share_permission_query(user_id: UUID, space_id: UUID, path: str | Ltree):
    return (
        select(func.coalesce(func.max(NodeShare.permission), 0))
        .join(
            Node,
            onclause=and_(
                NodeShare.node_id == Node.id,
                NodeShare.user_id == user_id,
                Node.space_id == space_id,
                Node.status != NodeStatus.DELETED,
            ),
        )
        .where(Node.path.op("@>")(path))
    )


def node_share_permission_list_query(user_id: UUID, space_id: UUID):
    return select(NodeShare.permission, Node.path).join(
        Node,
        onclause=and_(
            NodeShare.node_id == Node.id,
            NodeShare.user_id == user_id,
            Node.space_id == space_id,
            Node.status != NodeStatus.DELETED,
        ),
    )


def space_share_permission_query(user_id: UUID, space_id: UUID) -> Any:
    return select(func.coalesce(func.max(SpaceShare.permission), 0)).where(
        and_(
            SpaceShare.user_id == user_id,
            SpaceShare.space_id == space_id,
        )
    )


def logic_get_user_permission_on_space(db: Session, user_id: UUID, space_id: UUID):
    statement = space_share_permission_query(user_id, space_id)
    return db.execute(statement).scalar()


def logic_get_user_effective_permission_on_node(
    db: Session, user_id: UUID, space_id: UUID, node: Node | None = None
):
    if not node:
        return 0

    statement = node_share_permission_query(user_id, space_id, node.path)
    return db.execute(statement).scalar()


def logic_get_user_max_permission(
    db: Session, user_id: UUID, space_id: UUID, node: Node = None
):
    space_permission = logic_get_user_permission_on_space(db, user_id, space_id)
    node_permission = logic_get_user_effective_permission_on_node(
        db, user_id, space_id, node
    )
    return max(space_permission, node_permission)


def logic_user_satisfies_permission(
    db: Session,
    user_id: UUID,
    space: Space,
    node: Node | None = None,
    permission: int = SharePermission.READ,
):
    if space.owner_id == user_id:
        return True

    return logic_get_user_max_permission(db, user_id, space.id, node) >= permission
