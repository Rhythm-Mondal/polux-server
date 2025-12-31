from uuid import uuid4

from sqlalchemy import (
    Column,
    UUID,
    String,
    ForeignKey,
    Boolean,
    DateTime,
    func,
    UniqueConstraint,
)

from app.utils.database import Base


class Space(Base):
    __tablename__ = "spaces"
    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    owner_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (UniqueConstraint("owner_id", "name", name="uniq_space_name"),)
