from uuid import UUID

from sqlalchemy.orm import Session
from app import models, schemas


def get_user_spaces(db: Session, user_id: UUID) -> list[models.node.Space]:
    return db.query(models.node.Space).filter(models.node.Space.owner_id == user_id).all()


def create_user_space(db: Session, body: schemas.node.CreateSpace) -> models.node.Space:
    pass

def list_node_children(db: Session, node_id: int) -> schemas.node.ListNodeChildrenOut:
    pass