from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from api.database import Base

import uuid


class Category(Base):
    __tablename__ = "categories"

    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    path_id = Column(String(30), unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)

    problem = relationship("Problem", backref="category", cascade="all, delete-orphan")


class Problem(Base):
    __tablename__ = "problems"

    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    path_id = Column(String(30), unique=True, index=True, nullable=False)
    category_id = Column(
        UUIDType(binary=False),
        ForeignKey("categories.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    title = Column(String, nullable=False)
    statement = Column(Text, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    time_limit = Column(Float, default=2.0)
    memory_limit = Column(Integer, default=256)  # MB単位であることに注意

    testcase = relationship("Testcase", backref="problem", cascade="all, delete-orphan")


class Testcase(Base):
    __tablename__ = "testcases"

    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    problem_id = Column(
        UUIDType(binary=False),
        ForeignKey("problems.id", ondelete="CASCADE", onupdate="CASCADE"),
    )
    name = Column(String)
    input = Column(Text)
    output = Column(Text)
