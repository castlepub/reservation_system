from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import date, timedelta
import logging

from app.core.database import get_db
from app.models.user import User
from app.models.reservation import Reservation, ReservationStatus, ReservationType, DashboardNote
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
        priority=note_data.priority,
        author=current_user.username
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
    """Get all customers with their reservation statistics"""
    from app.models.room import Room
    
    # Get all unique customers from reservations
    reservations = db.query(Reservation).all()
    
    # Group by customer
    customers_dict = {}
    for reservation in reservations:
        email = reservation.email
        if email not in customers_dict:
            customers_dict[email] = {
                "customer_name": reservation.customer_name,
                "email": reservation.email,
                "phone": reservation.phone,
                "reservations": [],
                "created_at": reservation.created_at
            }
        customers_dict[email]["reservations"].append(reservation)
    
    # Convert to response format
    customer_responses = []
    for customer_data in customers_dict.values():
        reservations = customer_data["reservations"]
        last_visit = max(r.date for r in reservations) if reservations else None
        
        # Find most frequent room
        room_counts = {}
        for r in reservations:
            room_id = r.room_id
            if room_id:  # Only count if room_id exists
                room_counts[room_id] = room_counts.get(room_id, 0) + 1
        
        favorite_room_name = None
        if room_counts:
            favorite_room_id = max(room_counts.keys(), key=lambda k: room_counts[k])
            # Get room name from database
            room = db.query(Room).filter(Room.id == favorite_room_id).first()
            favorite_room_name = room.name if room else favorite_room_id
        
        customer_responses.append(CustomerResponse(
            customer_name=customer_data["customer_name"],
            email=customer_data["email"],
            phone=customer_data["phone"],
            total_reservations=len(reservations),
            last_visit=last_visit,
            favorite_room=favorite_room_name,
            created_at=customer_data["created_at"]
        ))
    
    return sorted(customer_responses, key=lambda x: x.created_at, reverse=True)


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
        
        # Base query for today's reservations
        query = db.query(Reservation).filter(Reservation.date == today)
        
        # Apply filters
        if reservation_type:
            query = query.filter(Reservation.reservation_type == reservation_type)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                Reservation.customer_name.ilike(search_term)
            )
        
        reservations = query.order_by(Reservation.time).all()
        
        # Convert to response format
        today_reservations = []
        for reservation in reservations:
            # Get actual table assignments from reservation_tables
            from app.models.reservation import ReservationTable
            from app.models.table import Table
            
            reservation_tables = db.query(ReservationTable).filter(
                ReservationTable.reservation_id == reservation.id
            ).all()
            
            table_names = []
            if reservation_tables:
                # Get table names from the table records
                for rt in reservation_tables:
                    table = db.query(Table).filter(Table.id == rt.table_id).first()
                    if table:
                        table_names.append(table.name)
            else:
                # Fallback if no table assignments found
                table_names = ["TBD"]
            
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
        logging.error(f"Today reservations error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading today's reservations: {str(e)}"
        ) 