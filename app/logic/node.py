import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import (
    select,
    and_,
    func,
    literal,
    desc,
    update,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased
from sqlalchemy_utils import Ltree

from app.logic.common import (
    logic_get_space_and_node,
    node_share_permission_list_query,
    logic_get_user_max_permission,
    logic_node_to_output_dict,
    logic_node_can_general,
)
from app.models.node import (
    Node,
    NodeStatus,
    NodeType,
)
from app.models.share import SharePermission
from app.schemas.node import (
    CreateFolder,
    ListFolderNodes,
    ListSpaceNodes,
    RenameNode,
    DeleteNode,
)


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
        and logic_get_user_max_permission(db, user_id, space_id) < SharePermission.READ
    ):
        raise HTTPException(status_code=404, detail="Space not found")

    statement = (
        db.query(Node)
        .filter(
            and_(
                Node.space_id == space_id,
                Node.parent_id.is_(None),
                Node.status == NodeStatus.ACTIVE,
            )
        )
        .order_by(Node.type, desc(Node.created_at))
    )
    if query.offset is not None:
        statement = statement.offset(query.offset)
    if query.limit is not None:
        statement = statement.limit(query.limit)
    db_nodes = statement.all()

    def output_mapper(node: Node):
        out = logic_node_to_output_dict(node)
        can = logic_node_can_general(node, SharePermission.MANAGE, True)
        out["can"] = can
        out["is_shared"] = False
        return out

    return list(map(output_mapper, db_nodes))


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

    def output_mapper(item: tuple[Node, int]):
        node, permission = item
        out = logic_node_to_output_dict(node)
        can = logic_node_can_general(node, permission, db_space.owner_id == user_id)
        out["can"] = can
        out["is_shared"] = db_space.owner_id != user_id  # TODO: needs better logic
        return out

    return list(map(output_mapper, db_nodes))


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
    return db.execute(statement).scalar() or 0


def logic_rename_node(
    db: Session, user_id, space_id: UUID, node_id: int, body: RenameNode
):
    db_space, db_node = logic_get_space_and_node(db, space_id, node_id)
    if (
        db_space.owner_id != user_id
        and logic_get_user_max_permission(db, user_id, space_id, db_node)
        < SharePermission.WRITE
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot rename this node"
        )
    if db_node.type != NodeStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{db_node.type.capitalize()} is archived",
        )

    try:
        db_node.name = body.name
        db.commit()
        return db_node
    except IntegrityError as e:
        logging.error(e)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A {db_node.type} with the same name already exists",
        )


def logic_archive_node(db: Session, user_id, space_id: UUID, node_id: int):
    db_space, db_node = logic_get_space_and_node(db, space_id, node_id)
    if (
        db_space.owner_id != user_id
        and logic_get_user_max_permission(db, user_id, space_id, db_node)
        < SharePermission.WRITE
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot rename this node"
        )

    if db_node.status != NodeStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{db_node.type.capitalize()} is already archived",
        )

    try:
        statement = (
            update(Node)
            .where(
                and_(
                    Node.path.op("<@")(db_node.path),
                    Node.space_id == space_id,
                )
            )
            .values(status=NodeStatus.ARCHIVED)
            .returning(Node.id)
        )
        ret = db.execute(statement).all()
        db.commit()
        return ret
    except Exception as e:
        logging.error(e)
        db.rollback()
        return None


def logic_delete_node(
    db: Session, user_id, space_id: UUID, node_id: int, query: DeleteNode
):
    db_space, db_node = logic_get_space_and_node(db, space_id, node_id)
    if db_space.owner_id != user_id:
        permission = logic_get_user_max_permission(db, user_id, space_id, db_node)
        status_code = (
            status.HTTP_403_FORBIDDEN if permission > 0 else status.HTTP_404_NOT_FOUND
        )
        details = (
            f"Only owners can delete {db_node.type}s"
            if permission > 0
            else "Node not found"
        )
        raise HTTPException(status_code=status_code, detail=details)

    total = db.query(Node).filter(Node.path.op("<@")(db_node.path)).count()
    if total > 1 and not query.recursive:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This folder contains content do you wish to delete them as well?",
        )

    try:
        statement = (
            update(Node)
            .where(Node.path.op("<@")(db_node.path))
            .values(status=NodeStatus.DELETED)
            .returning(Node.id)
        )
        ret = db.execute(statement).all()
        db.commit()
        return ret
    except Exception as e:
        logging.error(e)
        db.rollback()
        return None
