from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date, time
from app.models.reservation import ReservationStatus, ReservationType


class ReservationCreate(BaseModel):
    customer_name: str
    email: EmailStr
    phone: str
    party_size: int
    date: date
    time: time
    room_id: str
    reservation_type: Optional[ReservationType] = ReservationType.DINING
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
    reservation_type: Optional[ReservationType] = None
    notes: Optional[str] = None
    admin_notes: Optional[str] = None


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
    reservation_type: ReservationType
    notes: Optional[str]
    admin_notes: Optional[str]
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


# Dashboard-specific schemas
class DashboardNote(BaseModel):
    id: Optional[str] = None
    title: str
    content: str
    author: str
    priority: str = "normal"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_reservations_today: int
    total_guests_today: int
    total_reservations_week: int
    total_guests_week: int
    weekly_forecast: List[dict]  # Array of {date, reservations, guests}
    guest_notes: List[dict]  # Array of {customer_name, notes, date, reservation_type}


class CustomerResponse(BaseModel):
    customer_name: str
    email: str
    phone: str
    total_reservations: int
    last_visit: Optional[date]
    favorite_room: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TodayReservation(BaseModel):
    id: str
    customer_name: str
    time: time
    party_size: int
    table_names: List[str]
    reservation_type: ReservationType
    status: ReservationStatus
    notes: Optional[str]
    admin_notes: Optional[str]

    class Config:
        from_attributes = True 