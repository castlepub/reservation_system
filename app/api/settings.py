from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import time, datetime, timedelta
from app.core.database import get_db
from app.models.settings import WorkingHours, RestaurantSettings, DayOfWeek
from app.models.user import User
from app.schemas.settings import (
    WorkingHoursCreate, WorkingHoursUpdate, WorkingHoursResponse,
    RestaurantSettingCreate, RestaurantSettingUpdate, RestaurantSettingResponse,
    WeeklySchedule
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/working-hours", response_model=WeeklySchedule)
def get_working_hours(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get working hours for all days of the week"""
    working_hours = db.query(WorkingHours).all()
    
    # Ensure all days are represented
    existing_days = {wh.day_of_week for wh in working_hours}
    
    for day in DayOfWeek:
        if day not in existing_days:
            # Create default working hours (11:00 - 23:00)
            default_hours = WorkingHours(
                day_of_week=day,
                is_open=True,
                open_time=time(11, 0),
                close_time=time(23, 0)
            )
            db.add(default_hours)
            working_hours.append(default_hours)
    
    db.commit()
    
    # Sort by day order
    day_order = [
        DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY,
        DayOfWeek.THURSDAY, DayOfWeek.FRIDAY, DayOfWeek.SATURDAY, DayOfWeek.SUNDAY
    ]
    
    working_hours.sort(key=lambda x: day_order.index(x.day_of_week))
    
    return WeeklySchedule(working_hours=working_hours)


@router.put("/working-hours/{day_of_week}", response_model=WorkingHoursResponse)
def update_working_hours(
    day_of_week: DayOfWeek,
    hours_data: WorkingHoursUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update working hours for a specific day"""
    working_hours = db.query(WorkingHours).filter(
        WorkingHours.day_of_week == day_of_week
    ).first()
    
    if not working_hours:
        # Create new working hours entry
        working_hours = WorkingHours(day_of_week=day_of_week)
        db.add(working_hours)
    
    # Update fields
    if hours_data.is_open is not None:
        working_hours.is_open = hours_data.is_open
    
    if hours_data.open_time is not None:
        working_hours.open_time = hours_data.open_time
    
    if hours_data.close_time is not None:
        working_hours.close_time = hours_data.close_time
    
    # If closed, clear times
    if not working_hours.is_open:
        working_hours.open_time = None
        working_hours.close_time = None
    
    db.commit()
    db.refresh(working_hours)
    
    return working_hours


@router.get("/working-hours/{day_of_week}/time-slots")
def get_available_time_slots(
    day_of_week: DayOfWeek,
    db: Session = Depends(get_db)
):
    """Get available time slots for a specific day"""
    working_hours = db.query(WorkingHours).filter(
        WorkingHours.day_of_week == day_of_week
    ).first()
    
    if not working_hours or not working_hours.is_open:
        return {"time_slots": [], "message": f"Restaurant is closed on {day_of_week.value}"}
    
    # Generate time slots between open and close times
    open_time = working_hours.open_time
    close_time = working_hours.close_time
    
    if not open_time or not close_time:
        return {"time_slots": [], "message": f"Working hours not set for {day_of_week.value}"}
    
    time_slots = []
    current_time = datetime.combine(datetime.today(), open_time)
    end_time = datetime.combine(datetime.today(), close_time)
    
    # Generate 30-minute slots
    while current_time < end_time:
        time_slots.append(current_time.time().strftime("%H:%M"))
        current_time += timedelta(minutes=30)
    
    return {"time_slots": time_slots, "day": day_of_week.value}


@router.get("/restaurant", response_model=List[RestaurantSettingResponse])
def get_restaurant_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all restaurant settings"""
    settings = db.query(RestaurantSettings).all()
    
    # Create default settings if none exist
    if not settings:
        default_settings = [
            {
                "setting_key": "restaurant_name",
                "setting_value": "The Castle Pub",
                "description": "Restaurant name displayed throughout the system"
            },
            {
                "setting_key": "max_party_size",
                "setting_value": "20",
                "description": "Maximum number of people per reservation"
            },
            {
                "setting_key": "min_reservation_hours",
                "setting_value": "2",
                "description": "Minimum hours in advance for reservations"
            },
            {
                "setting_key": "max_reservation_days",
                "setting_value": "90",
                "description": "Maximum days in advance for reservations"
            },
            {
                "setting_key": "time_slot_duration",
                "setting_value": "30",
                "description": "Duration of each time slot in minutes"
            }
        ]
        
        for setting_data in default_settings:
            setting = RestaurantSettings(**setting_data)
            db.add(setting)
            settings.append(setting)
        
        db.commit()
    
    return settings


@router.put("/restaurant/{setting_key}", response_model=RestaurantSettingResponse)
def update_restaurant_setting(
    setting_key: str,
    setting_data: RestaurantSettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a specific restaurant setting"""
    setting = db.query(RestaurantSettings).filter(
        RestaurantSettings.setting_key == setting_key
    ).first()
    
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setting not found"
        )
    
    if setting_data.setting_value is not None:
        setting.setting_value = setting_data.setting_value
    
    if setting_data.description is not None:
        setting.description = setting_data.description
    
    db.commit()
    db.refresh(setting)
    
    return setting 