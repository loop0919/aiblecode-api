import uuid

from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from api.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    path_id = Column(String(30), unique=True, index=True, nullable=False)
    title = Column(String(50), nullable=False)
    description = Column(Text)

    problem = relationship("Problem", backref="category", cascade="all, delete-orphan")


class Problem(Base):
    __tablename__ = "problems"

    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    path_id = Column(String(30), index=True, nullable=False)
    category_id = Column(
        UUIDType(binary=False),
        ForeignKey("categories.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    title = Column(String(50), nullable=False)
    statement = Column(LONGTEXT, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    time_limit = Column(Float, default=2.0)
    memory_limit = Column(Integer, default=256)  # MB単位であることに注意

    testcase = relationship("Testcase", backref="problem", cascade="all, delete-orphan")

    # ユニーク制約を定義
    __table_args__ = (
        UniqueConstraint("path_id", "category_id", name="uq_path_category"),
    )


class Testcase(Base):
    __tablename__ = "testcases"

    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    problem_id = Column(
        UUIDType(binary=False),
        ForeignKey("problems.id", ondelete="CASCADE", onupdate="CASCADE"),
    )
    name = Column(String(50))
    input = Column(LONGTEXT)
    output = Column(LONGTEXT)
