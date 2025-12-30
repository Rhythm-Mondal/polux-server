import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, insert, update, and_, func, literal, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy_utils import Ltree

from app.models.node import (
    SharePermission,
    Space,
    Node,
    NodeShare,
    NodeShareExclusion,
    NodeStatus,
    NodeType,
)
from app.schemas.node import CreateFolder, ListFolderNodes, ListSpaceNodes


def user_satisfies_permission(
    db: Session,
    user_id: UUID,
    space_id: UUID,
    node_id: int | None = None,
    permission: int = SharePermission.READ,
):
    db_space = db.query(Space).filter(Space.id == space_id).first()
    if not db_space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Space not found"
        )

    if db_space.owner_id == user_id:
        return True

    db_node = (
        db.query(Node)
        .filter(and_(Node.id == node_id, Node.space_id == space_id))
        .first()
    )
    if not db_node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Node not found"
        )

    query = (
        select(func.coalesce(func.max(Space.permission), 0) > permission)
        .join(
            Node,
            onclause=and_(
                NodeShare.node_id == Node.id,
                Node.space_id == space_id,
                Node.status == NodeStatus.ACTIVE,
            ),
        )
        .outerjoin(
            NodeShareExclusion,
            onclause=and_(
                NodeShareExclusion.share_id == NodeShare.id,
                NodeShareExclusion.node_id == NodeShare.node_id,
            ),
        )
        .where(
            and_(
                NodeShare.user_id == user_id,
                Node.path.op("@>")(db_node.path),
            )
        )
    )

    return db.execute(query).scalar()


def create_space_folder(db: Session, user_id: UUID, space_id: UUID, body: CreateFolder):
    try:
        db_node = Node(
            space_id=space_id,
            parent_id=body.parent_id,
            uploader_id=user_id,
            name=body.name,
            type=NodeType.FOLDER,
        )
        db.add(db_node)
        db.commit()
    except IntegrityError as e:
        logging.error(e)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A folder with same name already exists",
        )
    except Exception as e:
        logging.error(e)
        db.rollback()
        return None

    try:
        if body.parent_id:
            db_parent = (
                db.query(Node)
                .filter(and_(Node.space_id == space_id, Node.id == body.parent_id))
                .first()
            )
            db_node.path = Ltree(f"{db_parent.path}.{db_node.id}")
        else:
            db_node.path = Ltree(str(db_node.id))
        db.commit()
        return db_node
    except IntegrityError as e:
        logging.error(e)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Node must be unique within the space",
        )
    except Exception as e:
        logging.error(e)
        db.rollback()
        return None


def list_user_space_nodes(db: Session, space_id: UUID, query: ListSpaceNodes):
    statement = (
        db.query(Node)
        .filter(
            and_(
                Node.space_id == space_id,
                Node.parent_id.is_(None),
                Node.status == NodeStatus.ACTIVE,
            )
        )
        .order_by(desc(Node.created_at))
    )
    if query.offset is not None:
        statement = statement.offset(query.offset)
    if query.limit is not None:
        statement = statement.limit(query.limit)
    db_nodes = statement.all()

    # TODO: better implementation
    def out_put_mapper(node: Node):
        return {
            "id": node.id,
            "space_id": node.space_id,
            "parent_id": node.parent_id,
            "name": node.name,
            "type": node.type,
            "uploader_id": node.uploader_id,
            "created_at": node.created_at,
            "updated_at": node.updated_at,
            "is_shared": False,
            "can": {
                "open": True,
                "upload": node.type == NodeType.FOLDER,
                "download": node.type == NodeType.FILE,
                "rename": True,
                "copy": True,
                "move": True,
                "paste": True,
                "archive": True,
                "delete": True,
                "share": True,
            },
        }

    return list(map(out_put_mapper, db_nodes))


def count_listed_user_space_nodes(db: Session, space_id: UUID):
    return (
        db.query(Node)
        .filter(
            and_(
                Node.space_id == space_id,
                Node.parent_id.is_(None),
                Node.status == NodeStatus.ACTIVE,
            )
        )
        .count()
    )
