from api.database import Base
from sqlalchemy import Boolean, Column, LargeBinary, String
from sqlalchemy_utils import UUIDType


import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(LargeBinary, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)
    token = Column(String, nullable=False)
