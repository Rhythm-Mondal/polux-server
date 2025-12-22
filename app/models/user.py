from uuid import uuid4
from sqlalchemy import Column, String, UUID
from app.utils.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(UUID, primary_key=True, default=uuid4, index=True)
    name = Column(String, index=True)
    email = Column(String, index=True)
    password = Column(String)
