from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.room import AreaType


class RoomBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    area_type: AreaType = AreaType.INDOOR
    priority: int = Field(default=5, ge=1, le=10)
    is_fallback_area: bool = False
    fallback_for: Optional[str] = None
    display_order: int = Field(default=0, ge=0)


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    area_type: Optional[AreaType] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    is_fallback_area: Optional[bool] = None
    fallback_for: Optional[str] = None
    display_order: Optional[int] = Field(None, ge=0)
    active: Optional[bool] = None


class RoomResponse(RoomBase):
    id: str
    active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 