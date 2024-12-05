import uuid
from datetime import datetime

from pytz import timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from api.database import Base


def get_current_time():
    return datetime.now(timezone("Asia/Tokyo"))


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    problem_id = Column(
        UUIDType(binary=False),
        ForeignKey("problems.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        UUIDType(binary=False),
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    language = Column(String(30), nullable=False)
    code = Column(Text, nullable=False)
    created_at = Column(DateTime, default=get_current_time, nullable=False)

    problem = relationship("Problem", backref="submission")
    user = relationship("User", backref="submission")


class SubmissionDetail(Base):
    __tablename__ = "submissions_details"

    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    submission_id = Column(
        UUIDType(binary=False),
        ForeignKey("submissions.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    testcase_id = Column(
        UUIDType(binary=False),
        ForeignKey("testcases.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    status = Column(String(10))
    time = Column(Float)
    memory = Column(Integer)

    submission = relationship("Submission", backref="submission_detail")
    testcase = relationship("Testcase", backref="submission_detail")
