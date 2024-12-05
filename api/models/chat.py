from datetime import datetime
from pytz import timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from api.database import Base

import uuid


def get_current_time():
    return datetime.now(timezone("Asia/Tokyo"))


class Chat(Base):
    __tablename__ = "chats"

    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUIDType(binary=False), ForeignKey("submissions.id"))
    is_ai = Column(Boolean, nullable=False)
    message = Column(Text)
    created_at = Column(DateTime, default=get_current_time, nullable=False)

    submission = relationship("Submission", backref="chat")
