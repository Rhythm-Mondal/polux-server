import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, insert, update, and_, func, literal, desc, text, cast, String
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
from app.schemas.node import CreateFolder, ListFolderNodes, ListSpaceNodes, MoveNode


def node_share_permission_sub_query(user_id: UUID, space_id: UUID, path: str | Ltree):
    return (
        select(func.coalesce(func.max(NodeShare.permission), 0))
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
                Node.path.op("@>")(path),
            )
        )
    )


def space_share_permission_sub_query(user_id: UUID, space_id: UUID):
    pass


def logic_user_satisfies_permission(
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

    result = False

    # space_share_resolve = space_share_permission_sub_query(user_id, space_id)
    # result = result or (db.execute(space_share_resolve).scalar() >= permission)

    if node_id is not None:
        db_node = (
            db.query(Node)
            .filter(and_(Node.id == node_id, Node.space_id == space_id))
            .first()
        )
        if not db_node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Node not found"
            )

        node_share_resolve = node_share_permission_sub_query(
            user_id, space_id, db_node.path
        )
        result = result or (db.execute(node_share_resolve).scalar() >= permission)

    return result


def logic_create_folder(db: Session, user_id: UUID, space_id: UUID, body: CreateFolder):
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


def logic_list_space_nodes(db: Session, space_id: UUID, query: ListSpaceNodes):
    statement = (
        db.query(Node)
        .filter(
            and_(
                Node.space_id == space_id,
                Node.status == NodeStatus.ACTIVE,
                func.nlevel(Node.path) == 1,
            )
        )
        .order_by(Node.type, desc(Node.created_at))
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
                "paste": node.type == NodeType.FOLDER,
                "archive": True,
                "delete": True,
                "share": True,
            },
        }

    return list(map(out_put_mapper, db_nodes))


def logic_count_listed_space_nodes(db: Session, space_id: UUID):
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


def logic_list_folder_nodes(db: Session, space_id: UUID, parent_id: int, query: ListFolderNodes):
    parent_node = (
        db.query(Node)
        .filter(
            and_(
                Node.space_id == space_id,
                Node.id == parent_id,
                Node.status == NodeStatus.ACTIVE
            )
        )
    ).first()
    if not parent_node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    if parent_node.type != NodeType.FOLDER:
        return []

    statement = (
        db.query(Node)
        .filter(
            and_(
                Node.space_id == space_id,
                Node.status == NodeStatus.ACTIVE,
                Node.path.op("~")(literal(f'{parent_node.path}.*{{1}}')),
            )
        )
        .order_by(Node.type, desc(Node.created_at))
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
                "paste": node.type == NodeType.FOLDER,
                "archive": True,
                "delete": True,
                "share": True,
            },
        }

    return list(map(out_put_mapper, db_nodes))


def logic_count_listed_folder_nodes(db: Session, space_id: UUID, parent_id: int):
    parent_node = (
        db.query(Node)
        .filter(
            and_(
                Node.space_id == space_id,
                Node.id == parent_id,
                Node.status == NodeStatus.ACTIVE
            )
        )
    ).first()
    if not parent_node or parent_node.type != NodeType.FOLDER:
        return 0

    return (
        db.query(Node)
        .filter(
            and_(
                Node.space_id == space_id,
                Node.status == NodeStatus.ACTIVE,
                Node.path.op("~")(literal(f'{parent_node.path}.*{{1}}')),
            )
        )
        .count()
    )


def logic_move_node(
    db: Session, user_id: UUID, space_id: UUID, node_id: int, body: MoveNode
):
    pass
