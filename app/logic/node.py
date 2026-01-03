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
    cast,
    bindparam,
    Boolean,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased
from sqlalchemy_utils import Ltree, LtreeType
from queue import Queue

from app.logic.common import (
    logic_get_space_and_node,
    node_share_permission_list_query,
    logic_get_user_max_permission,
    logic_node_to_output_dict,
    logic_node_can_general,
    logic_get_user_permission_on_space,
    logic_get_user_effective_permission_on_node,
)
from app.models.node import (
    Node,
    NodeStatus,
    NodeType,
)
from app.models.share import SharePermission
from app.models.space import Space
from app.schemas.node import (
    CreateFolder,
    ListFolderNodes,
    ListSpaceNodes,
    RenameNode,
    DeleteNode,
    MoveNode, CopyNode,
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
            detail="Node path must be unique within the space",
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
    if db_node.status != NodeStatus.ACTIVE:
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


def logic_resolve_move_permission(
        db: Session,
        user_id: UUID,
        space_id: UUID,
        src_node_id: int,
        dst_node_id: int | None = None,
):
    db_space = db.query(Space).filter(Space.id == space_id).first()
    if not db_space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Space not found"
        )

    src_node = (
        db.query(Node)
        .filter(
            and_(
                Node.space_id == space_id,
                Node.id == src_node_id,
                Node.status != NodeStatus.DELETED,
            )
        )
        .first()
    )
    dst_node = (
        db.query(Node)
        .filter(
            and_(
                Node.space_id == space_id,
                Node.id == dst_node_id,
                Node.status != NodeStatus.DELETED,
            )
        )
        .first()
    )

    if not src_node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Source not found"
        )

    if src_node.status != NodeStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Source is archived"
        )

    if not dst_node and dst_node_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Destination not found"
        )

    if dst_node:
        if dst_node.status != NodeStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Destination is archived",
            )
        if dst_node.type != NodeType.FOLDER:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Destination is not a folder",
            )

    if db_space.owner_id == user_id:
        return db_space, src_node, dst_node

    space_permission = logic_get_user_permission_on_space(db, user_id, space_id)
    src_node_permission = logic_get_user_effective_permission_on_node(
        db, user_id, space_id, src_node
    )
    dst_node_permission = logic_get_user_effective_permission_on_node(
        db, user_id, space_id, dst_node
    )

    if max(space_permission, src_node_permission) < SharePermission.WRITE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You not have permission to move this {src_node.type}",
        )

    if max(space_permission, dst_node_permission) < SharePermission.WRITE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You not have permission to move to this {src_node.type}",
        )

    return db_space, src_node, dst_node


def logic_move_node(
        db: Session, user_id: UUID, space_id: UUID, node_id: int, body: MoveNode
):
    db_space, db_src, db_dst = logic_resolve_move_permission(
        db, user_id, space_id, node_id, body.parent_id
    )

    old_path = str(db_src.path)
    new_path = f"{db_dst.path}.{db_src.id}" if body.parent_id else str(db_src.id)

    if db.execute(
            select(
                cast(Ltree(old_path), LtreeType)
                        .op("@>")(cast(Ltree(new_path), LtreeType))
                        .cast(Boolean)
            )
    ).scalar():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can not move to one self or children",
        )

    try:
        db_src.path = Ltree(new_path)
        db_src.parent_id = body.parent_id
        if body.name is not None:
            db_src.name = body.name

        statement = (
            update(Node)
            .where(
                and_(
                    Node.path.op("<@")(Ltree(old_path)),
                    Node.id != node_id,
                )
            )
            .values(
                path=literal(new_path).op("||")(
                    func.subpath(Node.path, func.nlevel(old_path))
                )
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
            detail=f"A {db_src.type} with same name already exists at destination rename this {db_src.type}?",
        )


def logic_resolve_copy_permission(
        db: Session,
        user_id: UUID,
        src_space_id: UUID,
        src_node_id: int,
        dst_space_id: UUID,
        dst_node_id: int | None = None,
) -> tuple[Space, Space, Node, Node]:
    src_space = db.query(Space).filter(Space.id == src_space_id).first()
    if not src_space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Source space not found"
        )

    src_node = (
        db.query(Node)
        .filter(
            and_(
                Node.space_id == src_space_id,
                Node.id == src_node_id,
                Node.status != NodeStatus.DELETED,
            )
        )
        .first()
    )
    dst_node = (
        db.query(Node)
        .filter(
            and_(
                Node.space_id == src_space_id,
                Node.id == dst_node_id,
                Node.status != NodeStatus.DELETED,
            )
        )
        .first()
    )

    if not src_node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Source node not found"
        )

    if src_node.status != NodeStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Source node is archived"
        )

    dst_space = src_space if src_space_id == dst_space_id else db.query(Space).filter(Space.id == dst_space_id).first()
    if not dst_space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Destination space not found"
        )

    if not dst_node and dst_node_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Destination node not found"
        )

    if dst_node:
        if dst_node.status != NodeStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Destination is archived",
            )
        if dst_node.type != NodeType.FOLDER:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Destination is not a folder",
            )

    if src_space.owner_id == dst_space.owner_id == user_id:
        return src_space, dst_space, src_node, dst_node

    src_space_permission = logic_get_user_permission_on_space(db, user_id, src_space_id)
    dst_space_permission = logic_get_user_permission_on_space(db, user_id, dst_space_id)
    src_node_permission = logic_get_user_effective_permission_on_node(
        db, user_id, src_space_id, src_node
    )
    dst_node_permission = logic_get_user_effective_permission_on_node(
        db, user_id, dst_space_id, dst_node
    )

    if max(src_space_permission, src_node_permission) < SharePermission.READ:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You not have permission to move this {src_node.type}",
        )

    if max(dst_space_permission, dst_node_permission) < SharePermission.WRITE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You not have permission to move to this {src_node.type}",
        )

    return src_space, dst_space, src_node, dst_node


def logic_get_subtree_for_copy(db: Session, user_id: UUID, src_node: Node):
    # TODO: implement share based exclusion logic
    return (
        db.query(Node)
        .filter(
            and_(
                Node.space_id == src_node.space_id,
                Node.path.op("<@")(src_node.path),
                Node.status == NodeStatus.ACTIVE
            )
        )
        .order_by(Node.path.nlevel())
    ).all()


def logic_copy_node(db: Session, user_id: UUID, space_id: UUID, node_id: int, body: CopyNode):
    src_space, dst_space, src_node, dst_node = logic_resolve_copy_permission(db, user_id, space_id, node_id,
                                                                             body.space_id, body.parent_id)

    old_v_new: dict[int, Node] = {}
    db_nodes = logic_get_space_and_node(db, user_id, src_node)

    try:
        with db.begin():
            head_node = Node(
                space_id=body.space_id,
                parent_id=body.parent_id,
                type=src_node.type,
                name=body.name if body.name else src_node.name,
                status=NodeStatus.ACTIVE,
                uploader_id=user_id
            )
            db.add(head_node)
            db.flush()

            head_node.path = (
                dst_node.path + Ltree(str(head_node.id))
                if dst_node else
                Ltree(str(head_node.id))
            )
            db.flush()

            old_v_new[node_id] = head_node

            for db_node in db_nodes[1:]:
                parent = old_v_new[db_node.parent_id]

                node = Node(
                    space_id=parent.space_id,
                    parent_id=parent.id,
                    type=db_node.type,
                    name=db_node.name,
                    status=NodeStatus.ACTIVE,
                    uploader_id=user_id
                )
                db.add(node)
                db.flush()

                node.path = parent.path + Ltree(str(node.id))
                db.flush()

                old_v_new[db_node.id] = node

        return old_v_new.values()
    except IntegrityError as e:
        logging.error(e)
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"A {src_node.type} with same name already exists at destination")
