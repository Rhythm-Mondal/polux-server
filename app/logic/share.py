from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import Session

from app.logic.common import logic_node_to_output_dict, logic_node_can_general
from app.models.node import Node, NodeStatus, NodeType
from app.models.share import SharePermission, NodeShare
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
