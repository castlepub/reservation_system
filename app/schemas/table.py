from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TableCreate(BaseModel):
    room_id: str
    name: str
    capacity: int
    combinable: bool = True
    public_bookable: bool = True
    x: Optional[int] = None
    y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None


class TableUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    combinable: Optional[bool] = None
    active: Optional[bool] = None
    public_bookable: Optional[bool] = None
    x: Optional[int] = None
    y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None


class TableResponse(BaseModel):
    id: str
    room_id: str
    name: str
    capacity: int
    combinable: bool
    public_bookable: bool
    active: bool
    x: Optional[int]
    y: Optional[int]
    width: Optional[int]
    height: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True 