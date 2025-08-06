from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base
import enum


class AreaType(str, enum.Enum):
    INDOOR = "indoor"
    OUTDOOR = "outdoor"
    SHARED = "shared"


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    active = Column(Boolean, default=True, nullable=False)
    
    # Area management (new features)
    area_type = Column(Enum(AreaType), default=AreaType.INDOOR, nullable=False)
    priority = Column(Integer, default=5)  # 1-10 priority for assignment order
    is_fallback_area = Column(Boolean, default=False)  # For weather-dependent assignments
    fallback_for = Column(Text, nullable=True)  # Room ID this can fallback to
    
    # Display order for drag-and-drop reordering
    display_order = Column(Integer, default=0)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    tables = relationship("Table", back_populates="room", cascade="all, delete-orphan")
    reservations = relationship("Reservation", back_populates="room")
    table_layouts = relationship("TableLayout", back_populates="room", cascade="all, delete-orphan")
    room_layout = relationship("RoomLayout", back_populates="room", uselist=False, cascade="all, delete-orphan") 