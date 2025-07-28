from sqlalchemy import Column, String, Integer, Date, Time, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base
import enum


class ReservationStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    party_size = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    room_id = Column(Text, ForeignKey("rooms.id"), nullable=False)
    status = Column(Enum(ReservationStatus), default=ReservationStatus.CONFIRMED, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    room = relationship("Room", back_populates="reservations")
    reservation_tables = relationship("ReservationTable", back_populates="reservation", cascade="all, delete-orphan")


class ReservationTable(Base):
    __tablename__ = "reservations_tables"

    id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    reservation_id = Column(Text, ForeignKey("reservations.id"), nullable=False)
    table_id = Column(Text, ForeignKey("tables.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    reservation = relationship("Reservation", back_populates="reservation_tables")
    table = relationship("Table", back_populates="reservation_tables") 