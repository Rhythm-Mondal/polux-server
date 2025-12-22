from uuid import uuid4

from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    String,
    Boolean,
    UUID,
    DateTime,
    func,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_utils import LtreeType

from app.utils.database import Base


class Node(Base):
    __tablename__ = "nodes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_id = Column(Integer, ForeignKey("nodes.id"), nullable=True, index=True)
    type = Column(String, index=True)
    name = Column(String, index=True)
    path = Column(LtreeType, index=True, nullable=False, unique=True)
    is_trashed = Column(Boolean, default=False)
    owner_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    uploader_id = Column(UUID, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (Index("idx_path_gist", "path", postgresql_using="gist"),)


class NodeStorage(Base):
    __tablename__ = "node_storages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    node = Column(Integer, ForeignKey("nodes.id"), nullable=False, index=True)
    service = Column(String, nullable=False)
    mimetype = Column(String, nullable=False)
    info = Column(JSONB, nullable=True)


class NodeUploadRequest(Base):
    __tablename__ = "node_upload_requests"
    id = Column(UUID, primary_key=True, default=uuid4, index=True)
    data = Column(JSONB, nullable=False)
    status = Column(String, nullable=False)
    expire_at = Column(DateTime)
