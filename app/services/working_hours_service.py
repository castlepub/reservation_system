from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import date, time, datetime, timedelta
from app.models.settings import WorkingHours, DayOfWeek


class WorkingHoursService:
    def __init__(self, db: Session):
        self.db = db

    def get_working_hours_for_day(self, day_of_week: DayOfWeek) -> Optional[WorkingHours]:
        """Get working hours for a specific day"""
        return self.db.query(WorkingHours).filter(
            WorkingHours.day_of_week == day_of_week
        ).first()

    def get_working_hours_for_date(self, target_date: date) -> Optional[WorkingHours]:
        """Get working hours for a specific date"""
        # Convert date to day of week
        day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        day_of_week = DayOfWeek(day_names[target_date.weekday()])
        
        return self.get_working_hours_for_day(day_of_week)

    def is_restaurant_open_on_date(self, target_date: date) -> bool:
        """Check if restaurant is open on a specific date"""
        working_hours = self.get_working_hours_for_date(target_date)
        
        if not working_hours:
            return False
        
        return working_hours.is_open

    def is_time_within_working_hours(self, target_date: date, target_time: time) -> bool:
        """Check if a specific time is within working hours"""
        working_hours = self.get_working_hours_for_date(target_date)
        
        if not working_hours or not working_hours.is_open:
            return False
        
        if not working_hours.open_time or not working_hours.close_time:
            return False
        
        # Handle cases where close time is after midnight
        if working_hours.close_time < working_hours.open_time:
            # Close time is after midnight (e.g., 02:00)
            return target_time >= working_hours.open_time or target_time <= working_hours.close_time
        else:
            # Normal case (e.g., 11:00 - 23:00)
            return working_hours.open_time <= target_time <= working_hours.close_time

    def get_available_time_slots(self, target_date: date, slot_duration_minutes: int = 30) -> List[str]:
        """Get available time slots for a specific date"""
        working_hours = self.get_working_hours_for_date(target_date)
        
        if not working_hours or not working_hours.is_open:
            return []
        
        if not working_hours.open_time or not working_hours.close_time:
            return []
        
        time_slots = []
        current_time = datetime.combine(target_date, working_hours.open_time)
        end_time = datetime.combine(target_date, working_hours.close_time)
        
        # Handle cases where close time is after midnight
        if working_hours.close_time < working_hours.open_time:
            # Add a day to end_time
            end_time = datetime.combine(target_date + timedelta(days=1), working_hours.close_time)
        
        # Generate time slots
        while current_time < end_time:
            time_slots.append(current_time.time().strftime("%H:%M"))
            current_time += timedelta(minutes=slot_duration_minutes)
        
        return time_slots

    def validate_reservation_time(self, target_date: date, target_time: time) -> Tuple[bool, str]:
        """Validate if a reservation time is within working hours"""
        if not self.is_restaurant_open_on_date(target_date):
            return False, f"Restaurant is closed on {target_date.strftime('%A, %B %d, %Y')}"
        
        if not self.is_time_within_working_hours(target_date, target_time):
            working_hours = self.get_working_hours_for_date(target_date)
            if working_hours and working_hours.open_time and working_hours.close_time:
                open_str = working_hours.open_time.strftime("%I:%M %p")
                close_str = working_hours.close_time.strftime("%I:%M %p")
                return False, f"Reservation time must be between {open_str} and {close_str}"
            else:
                return False, "Working hours not properly configured for this day"
        
        return True, "Time is valid"

    def get_working_hours_summary(self, target_date: date) -> dict:
        """Get a summary of working hours for a specific date"""
        working_hours = self.get_working_hours_for_date(target_date)
        
        if not working_hours:
            return {
                "is_open": False,
                "open_time": None,
                "close_time": None,
                "message": "Working hours not configured"
            }
        
        if not working_hours.is_open:
            return {
                "is_open": False,
                "open_time": None,
                "close_time": None,
                "message": "Restaurant is closed"
            }
        
        return {
            "is_open": True,
            "open_time": working_hours.open_time.strftime("%I:%M %p") if working_hours.open_time else None,
            "close_time": working_hours.close_time.strftime("%I:%M %p") if working_hours.close_time else None,
            "message": f"Open {working_hours.open_time.strftime('%I:%M %p')} - {working_hours.close_time.strftime('%I:%M %p')}" if working_hours.open_time and working_hours.close_time else "Hours not set"
        } 