from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date, time
from app.models.reservation import ReservationStatus


class ReservationCreate(BaseModel):
    customer_name: str
    email: EmailStr
    phone: str
    party_size: int
    date: date
    time: time
    room_id: str
    notes: Optional[str] = None


class ReservationUpdate(BaseModel):
    customer_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    party_size: Optional[int] = None
    date: Optional[date] = None
    time: Optional[time] = None
    room_id: Optional[str] = None
    status: Optional[ReservationStatus] = None
    notes: Optional[str] = None


class TableAssignment(BaseModel):
    table_id: str
    table_name: str
    capacity: int


class ReservationResponse(BaseModel):
    id: str
    customer_name: str
    email: str
    phone: str
    party_size: int
    date: date
    time: time
    room_id: str
    room_name: str
    status: ReservationStatus
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ReservationWithTables(ReservationResponse):
    tables: List[TableAssignment] = []


class AvailabilityRequest(BaseModel):
    date: date
    party_size: int
    room_id: Optional[str] = None


class TimeSlot(BaseModel):
    time: time
    available_tables: List[TableAssignment]
    total_capacity: int


class AvailabilityResponse(BaseModel):
    date: date
    party_size: int
    room_id: Optional[str]
    available_slots: List[TimeSlot] 