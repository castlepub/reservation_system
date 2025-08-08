from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Enum, Time
from sqlalchemy.sql import func
from app.core.database import Base
import enum
import uuid


class BlockScope(str, enum.Enum):
    GLOBAL = "global"
    ROOM = "room"
    TABLE = "table"


class BlockType(str, enum.Enum):
    BLACKOUT = "blackout"  # Explicit start/end window
    RELEASE = "release"    # Hide a day until a release time


class Recurrence(str, enum.Enum):
    NONE = "none"
    WEEKLY = "weekly"


class AvailabilityBlock(Base):
    __tablename__ = "availability_blocks"

    id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    scope = Column(Enum(BlockScope), nullable=False)
    target_id = Column(Text, nullable=True)  # room_id or table_id depending on scope

    block_type = Column(Enum(BlockType), nullable=False)

    # Blackout window
    start_datetime = Column(DateTime, nullable=True)
    end_datetime = Column(DateTime, nullable=True)

    # Release gate
    recurrence = Column(Enum(Recurrence), default=Recurrence.NONE, nullable=False)
    weekdays = Column(Text, nullable=True)  # comma-separated ints (0=Mon .. 6=Sun)
    release_time = Column(Time, nullable=True)

    timezone = Column(String, default="Europe/Berlin", nullable=False)
    reason = Column(Text, nullable=True)
    active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


