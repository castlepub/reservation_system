from sqlalchemy import Column, String, Integer, Time, Boolean, DateTime, Text, Enum
from sqlalchemy.sql import func
import uuid
from app.core.database import Base
import enum


class DayOfWeek(str, enum.Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class WorkingHours(Base):
    __tablename__ = "working_hours"

    id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    day_of_week = Column(Enum(DayOfWeek), nullable=False, unique=True)
    is_open = Column(Boolean, default=True, nullable=False)
    open_time = Column(Time, nullable=True)  # Can be null if closed
    close_time = Column(Time, nullable=True)  # Can be null if closed
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class RestaurantSettings(Base):
    __tablename__ = "restaurant_settings"

    id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    setting_key = Column(String, nullable=False, unique=True)
    setting_value = Column(Text, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now()) 