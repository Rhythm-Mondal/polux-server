import enum
from uuid import uuid4

from sqlalchemy import (
    ForeignKey,
    Column,
    Integer,
    String,
    UUID,
    DateTime,
    Enum,
    func,
    Index,
)
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_utils import LtreeType

from app.core.database import Base


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
    type = Column(
        Enum(
            NodeType,
            name="node_type",
            values_callable=lambda x: [e.value for e in x],
            create_type=False,
        ),
        nullable=False,
        index=True,
    )
    name = Column(String, index=True)
    path = Column(LtreeType, index=True)
    space_id = Column(UUID, ForeignKey("spaces.id"), nullable=False, index=True)
    uploader_id = Column(UUID, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    status = Column(
        Enum(
            NodeStatus,
            name="node_status",
            values_callable=lambda x: [e.value for e in x],
            create_type=False,
        ),
        server_default=NodeStatus.ACTIVE,
        index=True,
    )

    __table_args__ = (
        Index("idx_space_parent", "space_id", "parent_id"),
        Index("idx_space_status", "space_id", "status"),
        Index("idx_path_gist", "path", postgresql_using="gist"),
        Index(
            "uniq_space_path",
            "space_id",
            "path",
            unique=True,
            postgresql_where=(Column("path") != None),
        ),
        Index(
            "uniq_active_name",
            "parent_id",
            "name",
            "type",
            unique=True,
            postgresql_where=(Column("status") == str(NodeStatus.ACTIVE)),
            postgresql_nulls_not_distinct=True,
        ),
    )


class NodeStorageStatus(enum.StrEnum):
    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"


class NodeStorageService(enum.StrEnum):
    LOCAL = "local"
    S3 = "aws:s3"
    GCS = "gcp:gcs"


class NodeStorage(Base):
    __tablename__ = "node_storages"
    id = Column(UUID, primary_key=True, default=uuid4)
    node_id = Column(Integer, ForeignKey("nodes.id"), index=True)
    status = Column(
        Enum(
            NodeStorageStatus,
            name="node_storage_status",
            values_callable=lambda x: [e.value for e in x],
            create_type=False,
        ),
        server_default=NodeStorageStatus.PENDING,
    )
    service = Column(
        Enum(
            NodeStorageService,
            name="node_storage_service",
            values_callable=lambda x: [e.value for e in x],
            create_type=False,
        ),
    )
    key = Column(String)
    mime_type = Column(String)
    size_bytes = Column(BIGINT)
    checksum = Column(String)
    data = Column(JSONB)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


# class NodeUploadRequest(Base):
#     __tablename__ = "node_upload_requests"
#     id = Column(UUID, primary_key=True, default=uuid4)
#     data = Column(JSONB, nullable=False)
#     status = Column(String, nullable=False)
#     expire_at = Column(DateTime)
