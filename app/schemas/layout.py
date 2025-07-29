from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.table_layout import TableShape


class TableLayoutCreate(BaseModel):
    table_id: str
    room_id: str
    x_position: float
    y_position: float
    width: Optional[float] = 100.0
    height: Optional[float] = 80.0
    shape: Optional[TableShape] = TableShape.RECTANGULAR
    color: Optional[str] = "#4A90E2"
    border_color: Optional[str] = "#2E5BBA"
    text_color: Optional[str] = "#FFFFFF"
    show_capacity: Optional[bool] = True
    show_name: Optional[bool] = True
    font_size: Optional[int] = 12
    z_index: Optional[int] = 1


class TableLayoutUpdate(BaseModel):
    x_position: Optional[float] = None
    y_position: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    shape: Optional[TableShape] = None
    color: Optional[str] = None
    border_color: Optional[str] = None
    text_color: Optional[str] = None
    show_capacity: Optional[bool] = None
    show_name: Optional[bool] = None
    font_size: Optional[int] = None
    z_index: Optional[int] = None


class TableLayoutResponse(BaseModel):
    id: str
    table_id: str
    room_id: str
    x_position: float
    y_position: float
    width: float
    height: float
    shape: TableShape
    color: str
    border_color: str
    text_color: str
    show_capacity: bool
    show_name: bool
    font_size: int
    z_index: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class RoomLayoutCreate(BaseModel):
    room_id: str
    width: Optional[float] = 800.0
    height: Optional[float] = 600.0
    background_color: Optional[str] = "#F5F5F5"
    grid_enabled: Optional[bool] = True
    grid_size: Optional[int] = 20
    grid_color: Optional[str] = "#E0E0E0"
    show_entrance: Optional[bool] = True
    entrance_position: Optional[str] = "top"
    show_bar: Optional[bool] = False
    bar_position: Optional[str] = "center"


class RoomLayoutUpdate(BaseModel):
    width: Optional[float] = None
    height: Optional[float] = None
    background_color: Optional[str] = None
    grid_enabled: Optional[bool] = None
    grid_size: Optional[int] = None
    grid_color: Optional[str] = None
    show_entrance: Optional[bool] = None
    entrance_position: Optional[str] = None
    show_bar: Optional[bool] = None
    bar_position: Optional[str] = None


class RoomLayoutResponse(BaseModel):
    id: str
    room_id: str
    width: float
    height: float
    background_color: str
    grid_enabled: bool
    grid_size: int
    grid_color: str
    show_entrance: bool
    entrance_position: str
    show_bar: bool
    bar_position: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class TableWithLayout(BaseModel):
    id: str
    name: str
    capacity: int
    room_id: str
    room_name: str
    active: bool
    combinable: bool
    layout: Optional[TableLayoutResponse] = None

    class Config:
        from_attributes = True


class RoomWithLayout(BaseModel):
    id: str
    name: str
    active: bool
    layout: Optional[RoomLayoutResponse] = None
    tables: List[TableWithLayout] = []

    class Config:
        from_attributes = True


class DailyReservationView(BaseModel):
    id: str
    customer_name: str
    time: str
    duration_hours: int
    party_size: int
    table_names: List[str]
    reservation_type: str
    status: str
    notes: Optional[str]
    admin_notes: Optional[str]
    room_name: str

    class Config:
        from_attributes = True


class DailyViewResponse(BaseModel):
    date: str
    reservations: List[DailyReservationView]
    rooms: List[RoomWithLayout] 