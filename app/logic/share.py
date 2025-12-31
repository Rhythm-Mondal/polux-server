from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import Session

from app.models.node import Node, NodeShare, NodeStatus, NodeType, SharePermission
from app.schemas.share import ListSharedNodes


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

    def out_put_mapper(item: tuple[Node, int, UUID, datetime]):
        node, permission, sharer_id, shared_at = item
        return {
            "id": node.id,
            "space_id": node.space_id,
            "parent_id": node.parent_id,
            "name": node.name,
            "type": node.type,
            "uploader_id": node.uploader_id,
            "created_at": node.created_at,
            "updated_at": node.updated_at,
            "is_shared": True,
            "sharer_id": sharer_id,
            "shared_at": shared_at,
            "can": {
                "open": permission >= SharePermission.READ,
                "upload": node.type == NodeType.FOLDER
                and permission >= SharePermission.WRITE,
                "download": node.type == NodeType.FILE
                and permission >= SharePermission.READ,
                "rename": permission >= SharePermission.WRITE,
                "copy": permission >= SharePermission.READ,
                "move": permission >= SharePermission.WRITE,
                "paste": node.type == NodeType.FOLDER
                and permission >= SharePermission.WRITE,
                "archive": permission >= SharePermission.MANAGE,
                "delete": False,
                "share": permission >= SharePermission.MANAGE,
            },
        }

    return list(map(out_put_mapper, db_nodes))


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
