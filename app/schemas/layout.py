from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum


class TableShape(str, Enum):
    RECTANGULAR = "rectangular"
    ROUND = "round"
    SQUARE = "square"
    BAR_STOOL = "bar_stool"
    CUSTOM = "custom"


# Table Layout Schemas
class TableLayoutBase(BaseModel):
    x_position: float = Field(..., ge=0)
    y_position: float = Field(..., ge=0)
    width: float = Field(default=100.0, gt=0)
    height: float = Field(default=80.0, gt=0)
    shape: TableShape = TableShape.RECTANGULAR
    color: str = "#4A90E2"
    border_color: str = "#2E5BBA"
    text_color: str = "#FFFFFF"
    show_capacity: bool = True
    show_name: bool = True
    font_size: int = Field(default=12, ge=8, le=24)
    custom_capacity: Optional[int] = Field(None, ge=1, le=50)
    is_connected: bool = False
    connected_to: Optional[str] = None
    z_index: int = Field(default=1, ge=0)


class TableLayoutCreate(TableLayoutBase):
    # If table_id is not provided, the API will create a new table using the
    # provided table details (table_name, capacity, combinable)
    table_id: Optional[str] = None
    room_id: str
    # Optional fields to create a Table when table_id is not provided
    table_name: Optional[str] = None
    capacity: Optional[int] = Field(default=None, ge=1, le=50)
    combinable: Optional[bool] = True


class TableLayoutUpdate(BaseModel):
    x_position: Optional[float] = Field(None, ge=0)
    y_position: Optional[float] = Field(None, ge=0)
    width: Optional[float] = Field(None, gt=0)
    height: Optional[float] = Field(None, gt=0)
    shape: Optional[TableShape] = None
    color: Optional[str] = None
    border_color: Optional[str] = None
    text_color: Optional[str] = None
    show_capacity: Optional[bool] = None
    show_name: Optional[bool] = None
    font_size: Optional[int] = Field(None, ge=8, le=24)
    custom_capacity: Optional[int] = Field(None, ge=1, le=50)
    is_connected: Optional[bool] = None
    connected_to: Optional[str] = None
    z_index: Optional[int] = Field(None, ge=0)


class TableLayoutResponse(TableLayoutBase):
    id: str
    table_id: str
    room_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Room Layout Schemas
class RoomLayoutBase(BaseModel):
    width: float = Field(default=800.0, gt=0)
    height: float = Field(default=600.0, gt=0)
    background_color: str = "#F5F5F5"
    grid_enabled: bool = True
    grid_size: int = Field(default=20, ge=5, le=100)
    grid_color: str = "#E0E0E0"
    show_entrance: bool = True
    entrance_position: str = "top"  # top, bottom, left, right
    show_bar: bool = False
    bar_position: str = "center"


class RoomLayoutCreate(RoomLayoutBase):
    room_id: str


class RoomLayoutUpdate(BaseModel):
    width: Optional[float] = Field(None, gt=0)
    height: Optional[float] = Field(None, gt=0)
    background_color: Optional[str] = None
    grid_enabled: Optional[bool] = None
    grid_size: Optional[int] = Field(None, ge=5, le=100)
    grid_color: Optional[str] = None
    show_entrance: Optional[bool] = None
    entrance_position: Optional[str] = None
    show_bar: Optional[bool] = None
    bar_position: Optional[str] = None


class RoomLayoutResponse(RoomLayoutBase):
    id: str
    room_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Reservation schemas for layout integration
class ReservationSummary(BaseModel):
    id: str
    customer_name: str
    time: str
    duration_hours: int
    party_size: int
    reservation_type: str
    status: str
    notes: Optional[str] = None
    admin_notes: Optional[str] = None

    class Config:
        from_attributes = True


# Table with reservation data for layout editor
class TableWithReservation(BaseModel):
    layout_id: str
    table_id: str
    table_name: str
    capacity: int
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
    is_connected: bool
    connected_to: Optional[str]
    z_index: int
    reservations: List[ReservationSummary]

    class Config:
        from_attributes = True


# Layout Editor Data
class LayoutEditorData(BaseModel):
    room_id: str
    room_layout: RoomLayoutResponse
    tables: List[TableWithReservation]
    reservations: List[ReservationSummary]

    class Config:
        from_attributes = True


# Table Assignment Suggestions
class TableSuggestion(BaseModel):
    table_id: str
    table_name: str
    layout_id: str
    capacity: int
    x_position: float
    y_position: float
    shape: TableShape
    score: int  # Lower is better (closer fit)


# Export/Import schemas
class LayoutExport(BaseModel):
    room_id: str
    exported_at: str
    room_layout: Dict[str, Any]
    table_layouts: List[Dict[str, Any]]


class LayoutImport(BaseModel):
    layout_data: Dict[str, Any] 