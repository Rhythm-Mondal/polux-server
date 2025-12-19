from sqlalchemy import Column, Integer, String, UUID
from app.database import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(UUID, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, index=True)
    password = Column(String)