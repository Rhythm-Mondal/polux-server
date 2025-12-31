import logging
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import (
    select,
    and_,
    func,
    literal,
    desc,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased
from sqlalchemy_utils import Ltree

from app.models.node import (
    Node,
    NodeStatus,
    NodeType,
)
from app.models.share import SharePermission, NodeShare
from app.models.space import Space
from app.schemas.node import CreateFolder, ListFolderNodes, ListSpaceNodes


def node_share_permission_query(user_id: UUID, space_id: UUID, path: str | Ltree):
    return (
        select(func.coalesce(func.max(NodeShare.permission), 0))
        .join(
            Node,
            onclause=and_(
                NodeShare.node_id == Node.id,
                NodeShare.user_id == user_id,
                Node.space_id == space_id,
                Node.status == NodeStatus.ACTIVE,
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
            Node.status == NodeStatus.ACTIVE,
        ),
    )


def space_share_permission_sub_query(user_id: UUID, space_id: UUID) -> Any:
    pass


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


def logic_get_user_permission_on_space(db: Session, user_id: UUID, space_id: UUID):
    # Unimplemented
    # statement = space_share_permission_sub_query(user_id, space_id)
    # return db.execute(statement).scalar()
    return 0


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
    space_id: UUID,
    node_id: int | None = None,
    permission: int = SharePermission.READ,
):
    db_space, db_node = logic_get_space_and_node(db, space_id, node_id)

    if db_space.owner_id == user_id:
        return True

    return logic_get_user_max_permission(db, user_id, space_id, node_id) >= permission


def logic_create_folder(db: Session, user_id: UUID, space_id: UUID, body: CreateFolder):
    db_space, parent_node = logic_get_space_and_node(db, space_id, body.parent_id)
    if (
        db_space.owner_id != user_id
        and logic_get_user_max_permission(db, user_id, space_id, parent_node)
        < SharePermission.WRITE
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Space not found"
        )

    if body.parent_id:
        if parent_node.status != NodeStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Parent is archived"
            )
        if parent_node.type != NodeType.FOLDER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Parent is not a folder"
            )

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


def logic_list_space_nodes(
    db: Session, user_id: UUID, space_id: UUID, query: ListSpaceNodes
):
    db_space, _ = logic_get_space_and_node(db, space_id)
    if (
        db_space.owner_id != user_id
        and logic_get_user_permission_on_space(db, user_id, space_id)
        < SharePermission.READ
    ):
        raise HTTPException(status_code=404, detail="Space not found")

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
                "cut": True,
                "paste": node.type == NodeType.FOLDER,
                "archive": True,
                "delete": db_space.owner_id == user_id,
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


def logic_list_folder_nodes(
    db: Session, user_id, space_id: UUID, parent_id: int, query: ListFolderNodes
):
    db_space, parent_node = logic_get_space_and_node(db, space_id, parent_id)

    if parent_node.type != NodeType.FOLDER:
        return []

    X = aliased(Node)
    Y = aliased(node_share_permission_list_query(user_id, space_id).subquery())

    if db_space.owner_id != user_id:
        statement = (
            select(X, func.max(Y.c.permission).label("permission"))
            .outerjoin(Y, onclause=Y.c.path.op("@>")(X.path))
            .where(Y.c.permission.isnot(None))
        )
    else:
        statement = select(X, literal(SharePermission.MANAGE).label("permission"))

    statement = (
        statement.where(
            and_(
                X.status == NodeStatus.ACTIVE,
                X.parent_id == parent_id,
                X.space_id == space_id,
            )
        )
        .group_by(X.id)
        .order_by(X.type, desc(X.created_at))
    )
    if query.offset is not None:
        statement = statement.offset(query.offset)
    if query.limit is not None:
        statement = statement.limit(query.limit)
    db_nodes = db.execute(statement).all()

    # TODO: better implementation
    def out_put_mapper(item: tuple[Node, int]):
        node, permission = item

        return {
            "id": node.id,
            "space_id": node.space_id,
            "parent_id": node.parent_id,
            "name": node.name,
            "type": node.type,
            "uploader_id": node.uploader_id,
            "created_at": node.created_at,
            "updated_at": node.updated_at,
            "is_shared": db_space.owner_id != user_id,
            "can": {
                "open": permission >= SharePermission.READ,
                "upload": node.type == NodeType.FOLDER
                and permission >= SharePermission.WRITE,
                "download": node.type == NodeType.FILE
                and permission >= SharePermission.READ,
                "rename": permission >= SharePermission.WRITE,
                "copy": permission >= SharePermission.READ,
                "cut": permission >= SharePermission.WRITE,
                "paste": node.type == NodeType.FOLDER
                and permission >= SharePermission.WRITE,
                "archive": permission >= SharePermission.MANAGE,
                "delete": db_space.owner_id == user_id,
                "share": permission >= SharePermission.MANAGE,
            },
        }

    return list(map(out_put_mapper, db_nodes))


def logic_count_listed_folder_nodes(
    db: Session, user_id, space_id: UUID, parent_id: int
):
    db_space, parent_node = logic_get_space_and_node(db, space_id, parent_id)

    if parent_node.type != NodeType.FOLDER:
        return 0

    X = aliased(Node)
    Y = aliased(node_share_permission_list_query(user_id, space_id).subquery())

    statement = select(func.count(X.id))

    if db_space.owner_id != user_id:
        statement = statement.outerjoin(Y, onclause=Y.c.path.op("@>")(X.path)).where(
            Y.c.permission.isnot(None)
        )

    statement = statement.where(
        and_(
            X.status == NodeStatus.ACTIVE,
            X.parent_id == parent_id,
            X.space_id == space_id,
        )
    ).group_by(X.id)
    return db.execute(statement).scalar()
