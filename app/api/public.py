from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.reservation import (
    ReservationCreate, ReservationUpdate, ReservationWithTables,
    AvailabilityRequest, AvailabilityResponse
)
from app.schemas.room import RoomResponse
from app.services.reservation_service import ReservationService
from app.services.table_service import TableService
from app.services.email_service import EmailService
from app.models.room import Room

router = APIRouter(tags=["public"])


@router.post("/reservations", response_model=ReservationWithTables)
def create_reservation(
    reservation_data: ReservationCreate,
    db: Session = Depends(get_db)
):
    """Create a new reservation (public endpoint)"""
    try:
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
        # Validate party size
        if availability_request.party_size < 1 or availability_request.party_size > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Party size must be between 1 and 20"
            )
        
        # Validate duration
        duration = getattr(availability_request, 'duration_hours', 2)
        if duration not in [2, 3, 4]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duration must be 2, 3, or 4 hours"
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


@router.get("/rooms", response_model=List[RoomResponse])
def get_rooms(db: Session = Depends(get_db)):
    """Get all active rooms (public endpoint)"""
    rooms = db.query(Room).filter(Room.active == True).all()
    return rooms


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