from sqlalchemy import Column, Boolean, DateTime, ForeignKey, Text, Time, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base
from app.models.settings import DayOfWeek


class RoomBlockRule(Base):
    __tablename__ = "room_block_rules"

    id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id = Column(Text, ForeignKey("rooms.id"), nullable=False)
    day_of_week = Column(Enum(DayOfWeek), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    public_only = Column(Boolean, default=True, nullable=False)
    reason = Column(Text, nullable=True)
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    room = relationship("Room")


class TableBlockRule(Base):
    __tablename__ = "table_block_rules"

    id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    table_id = Column(Text, ForeignKey("tables.id"), nullable=False)
    day_of_week = Column(Enum(DayOfWeek), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    public_only = Column(Boolean, default=True, nullable=False)
    reason = Column(Text, nullable=True)
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    table = relationship("Table")


