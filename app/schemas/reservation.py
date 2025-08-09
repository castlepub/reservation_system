from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date, time
from app.models.reservation import ReservationStatus, ReservationType


class ReservationCreate(BaseModel):
    customer_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    party_size: int
    date: date
    time: time
    duration_hours: Optional[int] = 2  # Default 2 hours, can be 2, 3, or 4
    room_id: Optional[str] = None
    reservation_type: Optional[ReservationType] = ReservationType.DINING
    notes: Optional[str] = None
    admin_notes: Optional[str] = None


class ReservationUpdate(BaseModel):
    customer_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    party_size: Optional[int] = None
    date: Optional[date] = None
    time: Optional[time] = None
    duration_hours: Optional[int] = None
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
    duration_hours: int
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
    duration_hours: Optional[int] = 2
    room_id: Optional[str] = None
    # Optional time to narrow checks for specific room availability and block rules
    time: Optional[time] = None


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
    author: Optional[str] = None  # Will be set automatically by backend
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
    date: Optional[date] = None
    time: time
    party_size: int
    table_names: List[str]
    reservation_type: ReservationType
    status: ReservationStatus
    notes: Optional[str]
    admin_notes: Optional[str]

    class Config:
        from_attributes = True 


class UpcomingReservation(BaseModel):
    id: str
    customer_name: str
    date: date
    time: time
    party_size: int
    table_names: List[str]
    reservation_type: ReservationType
    status: ReservationStatus
    room_name: Optional[str] = None
    notes: Optional[str] = None
    admin_notes: Optional[str] = None

    class Config:
        from_attributes = True