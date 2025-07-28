from pydantic import BaseModel
from typing import Optional, List
from datetime import time
from app.models.settings import DayOfWeek


class WorkingHoursBase(BaseModel):
    day_of_week: DayOfWeek
    is_open: bool
    open_time: Optional[time] = None
    close_time: Optional[time] = None


class WorkingHoursCreate(WorkingHoursBase):
    pass


class WorkingHoursUpdate(BaseModel):
    is_open: Optional[bool] = None
    open_time: Optional[time] = None
    close_time: Optional[time] = None


class WorkingHoursResponse(WorkingHoursBase):
    id: str

    class Config:
        from_attributes = True


class RestaurantSettingBase(BaseModel):
    setting_key: str
    setting_value: str
    description: Optional[str] = None


class RestaurantSettingCreate(RestaurantSettingBase):
    pass


class RestaurantSettingUpdate(BaseModel):
    setting_value: Optional[str] = None
    description: Optional[str] = None


class RestaurantSettingResponse(RestaurantSettingBase):
    id: str

    class Config:
        from_attributes = True


class WeeklySchedule(BaseModel):
    working_hours: List[WorkingHoursResponse] 