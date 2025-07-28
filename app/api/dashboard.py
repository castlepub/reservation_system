from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, date, timedelta
from app.core.database import get_db
from app.models.reservation import Reservation, ReservationStatus, ReservationType, DashboardNote
from app.models.user import User
from app.schemas.reservation import (
    DashboardStats, DashboardNote as DashboardNoteSchema, 
    CustomerResponse, TodayReservation
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive dashboard statistics"""
    try:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
    
    # Today's stats
    today_reservations = db.query(Reservation).filter(
        and_(
            Reservation.date == today,
            Reservation.status == ReservationStatus.CONFIRMED
        )
    ).all()
    
    total_reservations_today = len(today_reservations)
    total_guests_today = sum(r.party_size for r in today_reservations)
    
    # Week's stats
    week_reservations = db.query(Reservation).filter(
        and_(
            Reservation.date >= week_start,
            Reservation.date <= week_end,
            Reservation.status == ReservationStatus.CONFIRMED
        )
    ).all()
    
    total_reservations_week = len(week_reservations)
    total_guests_week = sum(r.party_size for r in week_reservations)
    
    # Weekly forecast (next 7 days)
    weekly_forecast = []
    for i in range(7):
        forecast_date = today + timedelta(days=i)
        day_reservations = db.query(Reservation).filter(
            and_(
                Reservation.date == forecast_date,
                Reservation.status == ReservationStatus.CONFIRMED
            )
        ).all()
        
        weekly_forecast.append({
            "date": forecast_date.isoformat(),
            "day_name": forecast_date.strftime("%A"),
            "reservations": len(day_reservations),
            "guests": sum(r.party_size for r in day_reservations)
        })
    
    # Guest notes from recent reservations
    recent_reservations = db.query(Reservation).filter(
        and_(
            Reservation.date >= today - timedelta(days=7),
            Reservation.notes.isnot(None),
            Reservation.notes != ""
        )
    ).order_by(Reservation.created_at.desc()).limit(10).all()
    
    guest_notes = []
    for reservation in recent_reservations:
        guest_notes.append({
            "customer_name": reservation.customer_name,
            "notes": reservation.notes,
            "date": reservation.date.isoformat(),
            "reservation_type": reservation.reservation_type.value,
            "party_size": reservation.party_size
        })
    
        return DashboardStats(
            total_reservations_today=total_reservations_today,
            total_guests_today=total_guests_today,
            total_reservations_week=total_reservations_week,
            total_guests_week=total_guests_week,
            weekly_forecast=weekly_forecast,
            guest_notes=guest_notes
        )
    except Exception as e:
        import logging
        logging.error(f"Dashboard stats error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading dashboard stats: {str(e)}"
        )


@router.get("/notes", response_model=List[DashboardNoteSchema])
def get_dashboard_notes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all dashboard notes"""
    notes = db.query(DashboardNote).order_by(DashboardNote.created_at.desc()).all()
    return notes


@router.post("/notes", response_model=DashboardNoteSchema)
def create_dashboard_note(
    note_data: DashboardNoteSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new dashboard note"""
    note = DashboardNote(
        title=note_data.title,
        content=note_data.content,
        author=current_user.username,
        priority=note_data.priority
    )
    
    db.add(note)
    db.commit()
    db.refresh(note)
    
    return note


@router.delete("/notes/{note_id}")
def delete_dashboard_note(
    note_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a dashboard note"""
    note = db.query(DashboardNote).filter(DashboardNote.id == note_id).first()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    db.delete(note)
    db.commit()
    
    return {"message": "Note deleted successfully"}


@router.get("/customers", response_model=List[CustomerResponse])
def get_customers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all customers with their statistics"""
    # Group reservations by customer
    customers_data = db.query(
        Reservation.customer_name,
        Reservation.email,
        Reservation.phone,
        func.count(Reservation.id).label('total_reservations'),
        func.max(Reservation.date).label('last_visit'),
        func.min(Reservation.created_at).label('created_at')
    ).filter(
        Reservation.status == ReservationStatus.CONFIRMED
    ).group_by(
        Reservation.customer_name,
        Reservation.email,
        Reservation.phone
    ).all()
    
    customers = []
    for customer_data in customers_data:
        # Find favorite room (most frequent room_id)
        favorite_room = db.query(
            Reservation.room_id,
            func.count(Reservation.room_id).label('room_count')
        ).filter(
            and_(
                Reservation.customer_name == customer_data.customer_name,
                Reservation.email == customer_data.email
            )
        ).group_by(Reservation.room_id).order_by(func.count(Reservation.room_id).desc()).first()
        
        customers.append(CustomerResponse(
            customer_name=customer_data.customer_name,
            email=customer_data.email,
            phone=customer_data.phone,
            total_reservations=customer_data.total_reservations,
            last_visit=customer_data.last_visit,
            favorite_room=favorite_room.room_id if favorite_room else None,
            created_at=customer_data.created_at
        ))
    
    return customers


@router.get("/today", response_model=List[TodayReservation])
def get_today_reservations(
    reservation_type: Optional[ReservationType] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get today's reservations with filtering"""
    try:
        today = date.today()
    
    query = db.query(Reservation).filter(
        and_(
            Reservation.date == today,
            Reservation.status == ReservationStatus.CONFIRMED
        )
    )
    
    # Apply filters
    if reservation_type:
        query = query.filter(Reservation.reservation_type == reservation_type)
    
    if search:
        query = query.filter(
            or_(
                Reservation.customer_name.ilike(f"%{search}%"),
                Reservation.email.ilike(f"%{search}%"),
                Reservation.phone.ilike(f"%{search}%")
            )
        )
    
    reservations = query.order_by(Reservation.time).all()
    
    # Convert to TodayReservation format with table names
    today_reservations = []
    for reservation in reservations:
        table_names = [rt.table.name for rt in reservation.reservation_tables]
        
        today_reservations.append(TodayReservation(
            id=reservation.id,
            customer_name=reservation.customer_name,
            time=reservation.time,
            party_size=reservation.party_size,
            table_names=table_names,
            reservation_type=reservation.reservation_type,
            status=reservation.status,
            notes=reservation.notes,
            admin_notes=reservation.admin_notes
        ))
        
        return today_reservations
    except Exception as e:
        import logging
        logging.error(f"Today reservations error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading today's reservations: {str(e)}"
        ) 