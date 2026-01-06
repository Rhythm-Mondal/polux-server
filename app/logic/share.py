from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import Session

from app.logic.common import logic_node_to_output_dict, logic_node_can_general, logic_get_space_and_node, \
    logic_user_satisfies_permission
from app.models.node import Node, NodeStatus, NodeType
from app.models.share import SharePermission, NodeShare
from app.models.user import User
from app.schemas.share import ListSharedNodes, ShareNode, ListShares, DisplayPermission


def logic_permission_db_to_display(permission: int):
    mp = {
        SharePermission.READ: DisplayPermission.VIEWER,
        SharePermission.WRITE: DisplayPermission.EDITOR,
        SharePermission.MANAGE: DisplayPermission.ADMIN
    }
    return mp.get(permission)


def logic_permission_disp_to_db(permission: str | DisplayPermission):
    mp = {
        DisplayPermission.VIEWER: SharePermission.READ,
        DisplayPermission.EDITOR: SharePermission.WRITE,
        DisplayPermission.ADMIN: SharePermission.MANAGE
    }
    return mp.get(permission)


def logic_list_shared_nodes(db: Session, user_id: UUID, query: ListSharedNodes):
    statement = (
        select(Node, NodeShare.permission, NodeShare.sharer_id, NodeShare.shared_at)
        .join(
            Node,
            onclause=and_(
                Node.id == NodeShare.node_id,
                Node.status == NodeStatus.ACTIVE,
                NodeShare.user_id == user_id,
            ),
        )
        .order_by(desc(NodeShare.shared_at))
    )
    if query.offset is not None:
        statement = statement.offset(query.offset)
    if query.limit is not None:
        statement = statement.limit(query.limit)

    db_nodes = db.execute(statement).all()

    def output_mapper(item: tuple[Node, int, UUID, datetime]):
        node, permission, sharer_id, shared_at = item
        out = logic_node_to_output_dict(node)
        can = logic_node_can_general(node, permission, False)
        out["can"] = can
        out["is_shared"] = True
        out["sharer_id"] = sharer_id
        out["shared_at"] = shared_at
        return out

    return list(map(output_mapper, db_nodes))


def logic_count_listed_shared_nodes(db: Session, user_id: UUID):
    statement = select(func.count(NodeShare.id)).join(
        Node,
        onclause=and_(
            Node.id == NodeShare.node_id,
            Node.status == NodeStatus.ACTIVE,
            NodeShare.user_id == user_id,
        ),
    )
    return db.execute(statement).scalar()


def logic_get_shared_with_users(db: Session, user_id: UUID, space_id: UUID, node_id: int, query: ListShares):
    db_space, db_node = logic_get_space_and_node(db, space_id, node_id)
    if not logic_user_satisfies_permission(db, user_id, db_space, db_node, SharePermission.MANAGE):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to view share list")

    statement = (
        select(User.name, NodeShare.user_id, func.max(NodeShare.permission))
        .join(
            User,
            on=User.id == NodeShare.user_id
        )
        .join(
            NodeShare,
            onclause=and_(
                NodeShare.node_id == Node.id,
                Node.space_id == space_id,
                Node.status != NodeStatus.DELETED,
            )
        )
        .where(
            and_(
                Node.path.op("@>")(db_node.path)
            )
        )
        .group_by(NodeShare.user_id)
        .order_by(User.name)
    )
    if query.offset is not None:
        statement.offset(query.offset)
    if query.limit is not None:
        statement.limit(query.limit)

    res = db.execute(statement).all()

    def output_mapper(item: tuple[str, UUID, int]):
        return {
            "name": item[0],
            "user_id": item[1],
            "permission": DisplayPermission.OWNER if db_space.owner_id == item[1] else logic_permission_db_to_display(item[2])
        }

    return list(map(output_mapper, res))


def logic_share_node(db: Session, user_id: UUID, space_id: UUID, node_id: int, body: ShareNode):
    pass