from sqlalchemy import Column, String, Integer, Float, Boolean, Text, ForeignKey, Enum, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base
import enum


class TableShape(str, enum.Enum):
    RECTANGULAR = "rectangular"
    ROUND = "round"
    SQUARE = "square"
    BAR_STOOL = "bar_stool"
    CUSTOM = "custom"


class TableLayout(Base):
    __tablename__ = "table_layouts"

    id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    table_id = Column(Text, ForeignKey("tables.id"), nullable=False, unique=True)
    room_id = Column(Text, ForeignKey("rooms.id"), nullable=False)
    
    # Visual positioning
    x_position = Column(Float, nullable=False)  # X coordinate in the layout
    y_position = Column(Float, nullable=False)  # Y coordinate in the layout
    width = Column(Float, default=100.0)  # Width in pixels
    height = Column(Float, default=80.0)  # Height in pixels
    
    # Visual properties
    shape = Column(Enum(TableShape), default=TableShape.RECTANGULAR, nullable=False)
    color = Column(String, default="#4A90E2")  # Default blue color
    border_color = Column(String, default="#2E5BBA")
    text_color = Column(String, default="#FFFFFF")
    
    # Display properties
    show_capacity = Column(Boolean, default=True)
    show_name = Column(Boolean, default=True)
    font_size = Column(Integer, default=12)
    
    # Custom properties
    custom_capacity = Column(Integer)  # Override table capacity if needed
    is_connected = Column(Boolean, default=False)  # For connected tables
    connected_to = Column(Text, ForeignKey("table_layouts.id"), nullable=True)  # Link to another table
    
    # Z-index for layering
    z_index = Column(Integer, default=1)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    table = relationship("Table", back_populates="layout")
    room = relationship("Room", back_populates="table_layouts")


class RoomLayout(Base):
    __tablename__ = "room_layouts"

    id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id = Column(Text, ForeignKey("rooms.id"), nullable=False, unique=True)
    
    # Room layout properties
    width = Column(Float, default=800.0)  # Room width in pixels
    height = Column(Float, default=600.0)  # Room height in pixels
    background_color = Column(String, default="#F5F5F5")
    grid_enabled = Column(Boolean, default=True)
    grid_size = Column(Integer, default=20)
    grid_color = Column(String, default="#E0E0E0")
    
    # Room features
    show_entrance = Column(Boolean, default=True)
    entrance_position = Column(String, default="top")  # top, bottom, left, right
    show_bar = Column(Boolean, default=False)
    bar_position = Column(String, default="center")
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    room = relationship("Room", back_populates="room_layout") 