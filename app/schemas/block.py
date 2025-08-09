from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RoomBlockCreate(BaseModel):
    room_id: str
    starts_at: datetime
    ends_at: datetime
    reason: Optional[str] = None
    public_only: bool = True


class RoomBlockResponse(BaseModel):
    id: str
    room_id: str
    starts_at: datetime
    ends_at: datetime
    reason: Optional[str]
    public_only: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class TableBlockCreate(BaseModel):
    table_id: str
    starts_at: datetime
    ends_at: datetime
    reason: Optional[str] = None
    public_only: bool = True


class TableBlockResponse(BaseModel):
    id: str
    table_id: str
    starts_at: datetime
    ends_at: datetime
    reason: Optional[str]
    public_only: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


