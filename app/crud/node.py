from uuid import UUID

from sqlalchemy import exists, select, and_, or_
from sqlalchemy.orm import Session, aliased
from app import models, schemas


def visibility_exists(user_id: UUID, node_alias: models.node.Node):
    ShareRoot = aliased(models.node.Node)
    ShareExclude = aliased(models.node.NodeShareExclusion)

    return exists(
        select(1)
        .select_from(models.node.NodeShares)
        .join(ShareRoot, ShareRoot.id == models.node.NodeShares.node_id)
        .outerjoin(
            ShareExclude,
            and_(
                ShareExclude.share_id == models.node.NodeShares.id,
                ShareExclude.node_id == node_alias.id,
            ),
        )
        .where(
            models.node.NodeShares.user_id == user_id,
            ShareRoot.path.op("@>")(node_alias.path),
            ShareExclude.share_id.is_(None),
        )
    )


def get_user_spaces(db: Session, user_id: UUID) -> list[models.node.Space]:
    return (
        db.query(models.node.Space).filter(models.node.Space.owner_id == user_id).all()
    )


def create_user_space(db: Session, body: schemas.node.CreateSpace) -> models.node.Space:
    pass


def list_node_children(
    db: Session, user_id: UUID, space_id: UUID, node_id: int = None
) -> schemas.node.ListNodeChildrenOut:
    NodeAliase = aliased(models.node.Node)

    query = db.query(NodeAliase).filter(
        NodeAliase.space_id == space_id,
        NodeAliase.parent_id == node_id,
        NodeAliase.status == models.node.NodeStatus.ACTIVE,
        or_(
            exists(
                select(1)
                .select_from(models.node.Space)
                .where(
                    models.node.Space.id == space_id,
                    models.node.Space.owner_id == user_id,
                )
            ),
            visibility_exists(user_id, NodeAliase),
        ),
    )

    return query.all()
