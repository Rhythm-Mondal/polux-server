from uuid import uuid4

from sqlalchemy import (
    Column,
    UUID,
    Integer,
    ForeignKey,
    DateTime,
    func,
    CheckConstraint,
    Index,
)

from app.utils.database import Base


class SharePermission:
    READ = 10
    WRITE = 20
    MANAGE = 30


class SpaceShare(Base):
    __tablename__ = "space_shares"
    id = Column(UUID, primary_key=True, default=uuid4)
    space_id = Column(UUID, ForeignKey("spaces.id"), nullable=False, index=True)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    permission = Column(Integer, nullable=False)
    sharer_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    shared_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("permission in (10, 20, 30)"),
        Index("idx_share_user_space", "user_id", "space_id"),
    )


class NodeShare(Base):
    __tablename__ = "node_shares"
    id = Column(UUID, primary_key=True, default=uuid4)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False, index=True)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    permission = Column(Integer, nullable=False)
    sharer_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    shared_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("permission in (10, 20, 30)"),
        Index("idx_share_user_node", "user_id", "node_id"),
    )


class NodeShareExclusion(Base):
    __tablename__ = "node_share_exclusions"
    share_id = Column(UUID, ForeignKey("node_shares.id"), primary_key=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), primary_key=True)
