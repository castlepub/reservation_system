from pydantic import BaseModel
from typing import Optional
from datetime import datetime, time
from app.models.settings import DayOfWeek


class RoomBlockCreate(BaseModel):
    room_id: str
    starts_at: datetime
    ends_at: datetime
    reason: Optional[str] = None
    public_only: bool = True
    unlock_at: Optional[datetime] = None


class RoomBlockResponse(BaseModel):
    id: str
    room_id: str
    starts_at: datetime
    ends_at: datetime
    reason: Optional[str]
    public_only: bool
    unlock_at: Optional[datetime]
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
    unlock_at: Optional[datetime] = None


class TableBlockResponse(BaseModel):
    id: str
    table_id: str
    starts_at: datetime
    ends_at: datetime
    reason: Optional[str]
    public_only: bool
    unlock_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class RoomBlockRuleCreate(BaseModel):
    room_id: str
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    public_only: bool = True
    reason: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class RoomBlockRuleResponse(BaseModel):
    id: str
    room_id: str
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    public_only: bool
    reason: Optional[str]
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    
    class Config:
        from_attributes = True


class TableBlockRuleCreate(BaseModel):
    table_id: str
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    public_only: bool = True
    reason: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None


class TableBlockRuleResponse(BaseModel):
    id: str
    table_id: str
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    public_only: bool
    reason: Optional[str]
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    
    class Config:
        from_attributes = True


