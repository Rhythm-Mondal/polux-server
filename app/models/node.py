from uuid import uuid4
import enum

from sqlalchemy import (
    ForeignKey,
    Column,
    Integer,
    String,
    Boolean,
    UUID,
    DateTime,
    Enum,
    func,
    Index,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy_utils import LtreeType

from app.utils.database import Base


class Space(Base):
    __tablename__ = "spaces"
    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    owner_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint("owner_id", "name", name="uniq_space_name"),)


class NodeType(enum.StrEnum):
    FILE = "file"
    FOLDER = "folder"


class NodeStatus(enum.StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Node(Base):
    __tablename__ = "nodes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_id = Column(Integer, ForeignKey("nodes.id"), nullable=True, index=True)
    type = Column(Enum(NodeType), nullable=False, index=True)
    name = Column(String, index=True)
    path = Column(LtreeType, index=True, nullable=False)
    space_id = Column(UUID, ForeignKey("spaces.id"), nullable=False, index=True)
    uploader_id = Column(UUID, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    status = Column(Enum(NodeStatus), default=NodeStatus.ACTIVE, index=True)

    __table_args__ = (
        Index("idx_space_parent", "space_id", "parent_id"),
        Index("idx_space_status", "space_id", "status"),
        Index("idx_path_gist", "path", postgresql_using="gist"),
        UniqueConstraint("space_id", "path", name="uniq_space_path"),
    )


# class NodeStorage(Base):
#     __tablename__ = "node_storages"
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     node = Column(Integer, ForeignKey("nodes.id"), nullable=False, index=True)
#     service = Column(String, nullable=False)
#     mimetype = Column(String, nullable=False)
#     info = Column(JSONB, nullable=True)
#
#
# class NodeUploadRequest(Base):
#     __tablename__ = "node_upload_requests"
#     id = Column(UUID, primary_key=True, default=uuid4)
#     data = Column(JSONB, nullable=False)
#     status = Column(String, nullable=False)
#     expire_at = Column(DateTime)


class SharePermission:
    READ = 10
    WRITE = 20
    ADMIN = 30


class NodeShares(Base):
    __tablename__ = "node_shares"
    id = Column(UUID, primary_key=True, default=uuid4)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False, index=True)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    permission = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("permission in (10, 20, 30)"),
        Index("idx_share_user_node", "user_id", "node_id"),
    )


class NodeShareExclusion(Base):
    __tablename__ = "node_share_exclusions"
    share_id = Column(UUID, ForeignKey("shares.id"), primary_key=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), primary_key=True)
