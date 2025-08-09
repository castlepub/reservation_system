from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, date
from app.core.database import get_db
from app.schemas.reservation import (
    ReservationCreate, ReservationUpdate, ReservationWithTables,
    AvailabilityRequest, AvailabilityResponse
)
from app.schemas.room import RoomResponse
from app.services.reservation_service import ReservationService
from app.services.table_service import TableService
from app.services.working_hours_service import WorkingHoursService
from sqlalchemy import or_
from app.models.block import RoomBlock
from app.services.email_service import EmailService
from app.models.room import Room
# from app.models.room import AreaType  # Temporarily disabled
from app.models.settings import RestaurantSettings

router = APIRouter(tags=["public"])
@router.get("/public-settings")
def get_public_restaurant_settings(db: Session = Depends(get_db)):
    """Public endpoint to read non-sensitive restaurant settings (e.g., max_party_size)."""
    try:
        settings = db.query(RestaurantSettings).all()
        return [{"setting_key": s.setting_key, "setting_value": s.setting_value} for s in settings]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load settings: {str(e)}")


@router.get("/widget/config")
def get_widget_config(db: Session = Depends(get_db)):
    """Public endpoint to return safe widget theming and limits for embed usage."""
    try:
        settings_rows = db.query(RestaurantSettings).all()
        settings_map = {row.setting_key: row.setting_value for row in settings_rows}

        from app.core.config import settings as env_settings

        def get(key: str, default: str):
            return settings_map.get(key, default)

        return {
            "title": get("widget_title", "Booking"),
            "subtitle": get("widget_subtitle", "Reserve a Space at The Castle Pub"),
            "intro_text": get("widget_intro_text", "Reservations are free. Please order all food & drinks at the bar. No outside food/drinks allowed (birthday cakes okay)."),
            "default_language": get("widget_default_language", "en"),
            "colors": {
                "primary": get("widget_primary_color", "#22c55e"),
                "accent": get("widget_accent_color", "#16a34a"),
                "background": get("widget_background_color", "#111827"),
                "text": get("widget_text_color", "#f9fafb"),
            },
            "border_radius": int(get("widget_border_radius", "12") or 12),
            "limits": {
                "max_party_size": int(get("max_party_size", str(env_settings.MAX_PARTY_SIZE)) or env_settings.MAX_PARTY_SIZE),
                "min_advance_hours": int(get("min_advance_hours", str(env_settings.MIN_RESERVATION_HOURS)) or env_settings.MIN_RESERVATION_HOURS),
                "max_reservation_days": int(get("max_reservation_days", str(env_settings.MAX_RESERVATION_DAYS)) or env_settings.MAX_RESERVATION_DAYS),
                "time_slot_duration": int(get("time_slot_duration", "30") or 30),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load widget config: {str(e)}")


@router.post("/reservations", response_model=ReservationWithTables)
def create_reservation(
    reservation_data: ReservationCreate,
    db: Session = Depends(get_db)
):
    """Create a new reservation (public endpoint)"""
    try:
        # Public bookings must include an email so we can send confirmation and manage changes
        if not getattr(reservation_data, 'email', None):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required for public reservations"
            )
        reservation_service = ReservationService(db)
        reservation = reservation_service.create_reservation(reservation_data)
        
        # Send confirmation email
        email_service = EmailService()
        email_service.send_reservation_confirmation(reservation)
        
        return reservation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/availability", response_model=AvailabilityResponse)
def check_availability(
    availability_request: AvailabilityRequest,
    db: Session = Depends(get_db)
):
    """Check availability for a specific date, party size, and duration"""
    try:
        # Validate party size (use DB-max if present)
        try:
            max_party_setting = db.query(RestaurantSettings).filter(RestaurantSettings.setting_key == "max_party_size").first()
            max_party_size = int(max_party_setting.setting_value) if max_party_setting and str(max_party_setting.setting_value).isdigit() else 20
        except Exception:
            max_party_size = 20
        if availability_request.party_size < 1 or availability_request.party_size > max_party_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Party size must be between 1 and {max_party_size}"
            )
        
        # Validate duration - allow "until-end" as a special case
        duration = getattr(availability_request, 'duration_hours', 2)
        if duration not in [2, 3, 4] and duration != "until-end":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duration must be 2, 3, 4 hours, or 'until-end'"
            )
        
        table_service = TableService(db)
        
        if availability_request.room_id:
            # Check specific room
            room = db.query(Room).filter(Room.id == availability_request.room_id, Room.active == True).first()
            if not room:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Room not found"
                )
            # Check for active public room block for that slot
            from datetime import datetime, timedelta, time as time_cls
            start_dt = datetime.combine(availability_request.date, availability_request.time)
            end_dt = start_dt + timedelta(hours=duration)
            room_block = None
            try:
                room_block = db.query(RoomBlock).filter(
                    RoomBlock.room_id == availability_request.room_id,
                    RoomBlock.starts_at < end_dt,
                    RoomBlock.ends_at > start_dt,
                    RoomBlock.public_only == True,
                    or_(RoomBlock.unlock_at == None, RoomBlock.unlock_at > datetime.utcnow()),
                ).first()
            except Exception:
                room_block = None
            if room_block:
                return AvailabilityResponse(
                    date=availability_request.date,
                    party_size=availability_request.party_size,
                    room_id=availability_request.room_id,
                    available_slots=[],
                )
            
            time_slots = table_service.get_availability_for_date(
                availability_request.room_id, 
                availability_request.date, 
                availability_request.party_size,
                duration
            )
            
            return AvailabilityResponse(
                date=availability_request.date,
                party_size=availability_request.party_size,
                room_id=availability_request.room_id,
                available_slots=time_slots
            )
        else:
            # Check all active rooms
            rooms = db.query(Room).filter(Room.active == True).all()
            all_time_slots = []
            
            for room in rooms:
                room_slots = table_service.get_availability_for_date(
                    str(room.id), 
                    availability_request.date, 
                    availability_request.party_size,
                    duration
                )
                all_time_slots.extend(room_slots)
            
            # Sort by time
            all_time_slots.sort(key=lambda x: x.time)
            
            return AvailabilityResponse(
                date=availability_request.date,
                party_size=availability_request.party_size,
                room_id=None,
                available_slots=all_time_slots
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking availability: {str(e)}"
        )


@router.get("/availability/smart")
def get_smart_availability(
    date: str,
    party_size: int,
    preferred_area_type: str = None,
    reservation_type: str = "dinner",
    db: Session = Depends(get_db)
):
    """Get smart availability with intelligent area recommendations"""
    try:
        # Parse date
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        
        # Parse area type if provided
        area_type = None
        if preferred_area_type:
            # Temporarily disabled area type validation
            pass
            # try:
            #     area_type = AreaType(preferred_area_type.lower())
            # except ValueError:
            #     raise HTTPException(
            #         status_code=status.HTTP_400_BAD_REQUEST,
            #         detail=f"Invalid area type: {preferred_area_type}. Must be one of: indoor, outdoor, shared"
            #     )
        
        reservation_service = ReservationService(db)
        availability = reservation_service.get_smart_availability(
            date=target_date,
            party_size=party_size,
            preferred_area_type=area_type,
            reservation_type=reservation_type
        )
        
        return availability
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Temporarily disabled area recommendations endpoint
# @router.get("/areas/recommendations")
# def get_area_recommendations(
#     party_size: int,
#     reservation_type: str = "dinner",
#     db: Session = Depends(get_db)
# ):
#     """Get area recommendations based on party size and reservation type"""
#     try:
#         from app.services.area_service import AreaService
#         area_service = AreaService(db)
#         recommendations = area_service.get_area_recommendations(party_size, reservation_type)
#         return recommendations
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error getting area recommendations: {str(e)}"
#         )


@router.get("/rooms", response_model=List[RoomResponse])
def get_rooms(db: Session = Depends(get_db)):
    """Get all active rooms (public endpoint)"""
    try:
        rooms = db.query(Room).filter(Room.active == True).all()
        return rooms
    except Exception as e:
        print(f"Database connection failed in /api/rooms: {e}")
        # Return fallback data when database is not accessible
        from datetime import datetime
        return [
            {
                "id": "fallback-room-1",
                "name": "Main Dining Room",
                "description": "Main dining area",
                "active": True,
                "created_at": datetime.utcnow(),
                "updated_at": None
            },
            {
                "id": "fallback-room-2", 
                "name": "Private Dining",
                "description": "Private dining room",
                "active": True,
                "created_at": datetime.utcnow(),
                "updated_at": None
            }
        ]


@router.get("/working-hours/{date}")
def get_working_hours_for_date(date: str, db: Session = Depends(get_db)):
    """Get working hours for a specific date (public endpoint)"""
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        working_hours_service = WorkingHoursService(db)
        
        # Get working hours summary
        summary = working_hours_service.get_working_hours_summary(target_date)
        
        # Get available time slots if open
        time_slots = []
        if summary["is_open"]:
            time_slots = working_hours_service.get_available_time_slots(target_date)
        
        return {
            "date": date,
            "summary": summary,
            "available_time_slots": time_slots
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )


@router.put("/reservations/{token}", response_model=ReservationWithTables)
def update_reservation_by_token(
    token: str,
    update_data: ReservationUpdate,
    db: Session = Depends(get_db)
):
    """Update a reservation using a secure token"""
    from app.api.deps import get_reservation_by_token
    
    reservation = get_reservation_by_token(token, db)
    reservation_service = ReservationService(db)
    
    try:
        updated_reservation = reservation_service.update_reservation(str(reservation.id), update_data)
        
        if updated_reservation:
            # Send update email
            email_service = EmailService()
            email_service.send_reservation_update(updated_reservation, "Reservation details updated")
            
            return updated_reservation
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reservation not found"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/reservations/{token}")
def cancel_reservation_by_token(
    token: str,
    db: Session = Depends(get_db)
):
    """Cancel a reservation using a secure token"""
    from app.api.deps import get_reservation_by_token
    
    reservation = get_reservation_by_token(token, db)
    reservation_service = ReservationService(db)
    
    # Get reservation details before cancellation for email
    reservation_details = reservation_service.get_reservation(str(reservation.id))
    
    if reservation_service.cancel_reservation(str(reservation.id)):
        # Send cancellation email
        if reservation_details:
            email_service = EmailService()
            email_service.send_reservation_cancellation(reservation_details)
        
        return {"message": "Reservation cancelled successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        ) 


@router.get("/reservations")
def get_reservations(
    db: Session = Depends(get_db)
):
    """Get all reservations (public endpoint)"""
    try:
        from app.models.reservation import Reservation
        reservations = db.query(Reservation).all()
        return reservations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get reservations: {str(e)}"
        ) 