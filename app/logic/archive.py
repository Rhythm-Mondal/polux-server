import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, update, select, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased

from app.logic.common import (
    logic_get_space_and_node,
    logic_user_satisfies_permission,
    logic_node_to_output_dict,
    logic_node_can_general,
    logic_node_can_archive,
)
from app.models.node import Node, NodeStatus, NodeType
from app.models.share import SharePermission
from app.schemas.archive import RestoreNode, ListArchive


def logic_list_archive(db: Session, user_id: UUID, space_id: UUID, query: ListArchive):
    db_space, db_node = logic_get_space_and_node(db, space_id, query.node_id)
    if not logic_user_satisfies_permission(
        db, user_id, db_space, db_node, SharePermission.MANAGE
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission view archives",
        )

    if db_node and db_node.type != NodeType.FOLDER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Parent is not a folder"
        )

    L = aliased(Node)
    R = aliased(Node)

    statement = select(L)
    if query.node_id is None:
        statement = statement.outerjoin(
            R, onclause=and_(L.parent_id == R.id, R.status == NodeStatus.ACTIVE)
        ).where(or_(R.status == NodeStatus.ACTIVE, L.parent_id.is_(None)))
    else:
        statement = statement.where(L.parent_id == query.node_id)
    statement = statement.where(
        and_(L.status == NodeStatus.ARCHIVED, L.space_id == space_id)
    ).order_by(L.type, L.name)
    if query.offset is not None:
        statement.offset(query.offset)
    if query.limit is not None:
        statement.limit(query.limit)
    db_nodes = db.execute(statement).all()

    def output_mapper(item: tuple[Node, ...]):
        node, *_ = item
        out = logic_node_to_output_dict(node)
        can = logic_node_can_archive(
            node, SharePermission.MANAGE, db_space.owner_id == user_id
        )
        out["can"] = can
        out["is_shared"] = False
        return out

    return list(map(output_mapper, db_nodes))


def logic_count_listed_archive(db: Session, space_id: UUID, query: ListArchive):
    L = aliased(Node)
    R = aliased(Node)

    statement = select(func.count(L.id))
    if query.node_id is None:
        statement = statement.outerjoin(
            R, onclause=and_(L.parent_id == R.id, R.status == NodeStatus.ACTIVE)
        ).where(or_(R.status == NodeStatus.ACTIVE, L.parent_id.is_(None)))
    else:
        statement = statement.where(L.parent_id == query.node_id)
    statement = statement.where(
        and_(L.status == NodeStatus.ARCHIVED, L.space_id == space_id)
    )
    return db.execute(statement).scalar() or 0


def logic_restore_node(
    db: Session, user_id: UUID, space_id: UUID, node_id: int, body: RestoreNode
):
    db_space, db_node = logic_get_space_and_node(db, space_id, node_id)
    if not logic_user_satisfies_permission(
        db, user_id, db_space, db_node, SharePermission.MANAGE
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have permission to restore this node",
        )

    if db_node.status == NodeStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This node is already active",
        )

    highest_archived_ancestor = (
        db.query(Node)
        .filter(
            and_(
                Node.space_id == space_id,
                Node.path.op("@>")(db_node.path),
                Node.status == NodeStatus.ARCHIVED,
            )
        )
        .order_by(func.nlevel(Node.path))
        .first()
    )

    if highest_archived_ancestor.id != db_node.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": f"Parent is also archived, restore folder:{highest_archived_ancestor.name} first",
                "node_id": highest_archived_ancestor.id,
            },
        )

    try:
        db_node.status = NodeStatus.ACTIVE
        if body.name:
            db_node.name = body.name
        if body.overwrite:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Overwrite is unimplemented",
            )
        # db.commit()
        statement = (
            update(Node)
            .where(
                and_(
                    Node.path.op("<@")(db_node.path),
                    Node.path != db_node.path,
                    Node.space_id == space_id,
                )
            )
            .values(
                status=NodeStatus.ACTIVE,
            )
            .returning(Node.id)
        )
        ret = db.execute(statement).all()
        db.commit()
        return ret
    except IntegrityError as e:
        logging.error(e)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A {db_node.type} with the same name already exists, rename on restore",
        )
