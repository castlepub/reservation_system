from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    tables = relationship("Table", back_populates="room", cascade="all, delete-orphan")
    reservations = relationship("Reservation", back_populates="room") 