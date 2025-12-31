import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.logic.common import logic_get_space_and_node, logic_user_satisfies_permission
from app.models.node import Node, NodeStatus
from app.models.share import SharePermission
from app.schemas.archive import RestoreNode


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
