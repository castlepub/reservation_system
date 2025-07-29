from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base


class Table(Base):
    __tablename__ = "tables"

    id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id = Column(Text, ForeignKey("rooms.id"), nullable=False)
    name = Column(String, nullable=False)  # e.g., "T1", "Table 1"
    capacity = Column(Integer, nullable=False)
    combinable = Column(Boolean, default=True, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    
    # Layout coordinates (for future drag/drop interface)
    x = Column(Integer)
    y = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    room = relationship("Room", back_populates="tables")
    reservation_tables = relationship("ReservationTable", back_populates="table", cascade="all, delete-orphan")
    layout = relationship("TableLayout", back_populates="table", uselist=False, cascade="all, delete-orphan") 