from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.room import RoomCreate, RoomUpdate, RoomResponse
from app.schemas.table import TableCreate, TableUpdate, TableResponse
from app.schemas.reservation import ReservationUpdate, ReservationWithTables
from app.schemas.user import UserCreate, UserResponse
from app.services.reservation_service import ReservationService
from app.services.pdf_service import PDFService
from app.models.room import Room
from app.models.table import Table
from app.models.user import User
from app.api.deps import get_current_staff_user, get_current_admin_user
from datetime import date
import uuid

router = APIRouter(prefix="/admin", tags=["admin"])


# Room Management
@router.post("/rooms", response_model=RoomResponse)
def create_room(
    room_data: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Create a new room"""
    room = Room(
        name=room_data.name,
        description=room_data.description
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.get("/rooms", response_model=List[RoomResponse])
def get_rooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Get all rooms"""
    rooms = db.query(Room).all()
    return rooms


@router.get("/rooms/{room_id}", response_model=RoomResponse)
def get_room(
    room_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Get a specific room"""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.put("/rooms/{room_id}", response_model=RoomResponse)
def update_room(
    room_id: str,
    room_data: RoomUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Update a room"""
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    for field, value in room_data.dict(exclude_unset=True).items():
        setattr(room, field, value)
    
    db.commit()
    db.refresh(room)
    return room


# Table Management
@router.post("/tables", response_model=TableResponse)
def create_table(
    table_data: TableCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Create a new table"""
    table = Table(
        room_id=table_data.room_id,
        name=table_data.name,
        capacity=table_data.capacity,
        combinable=table_data.combinable,
        x=table_data.x,
        y=table_data.y,
        width=table_data.width,
        height=table_data.height
    )
    db.add(table)
    db.commit()
    db.refresh(table)
    return table


@router.get("/tables", response_model=List[TableResponse])
def get_tables(
    room_id: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Get all tables, optionally filtered by room"""
    query = db.query(Table)
    if room_id:
        query = query.filter(Table.room_id == room_id)
    tables = query.all()
    return tables


@router.put("/tables/{table_id}", response_model=TableResponse)
def update_table(
    table_id: str,
    table_data: TableUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Update a table"""
    table = db.query(Table).filter(Table.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    
    for field, value in table_data.dict(exclude_unset=True).items():
        setattr(table, field, value)
    
    db.commit()
    db.refresh(table)
    return table


# Reservation Management
@router.get("/reservations", response_model=List[ReservationWithTables])
def get_reservations(
    date: str = None,
    room_id: str = None,
    customer_name: str = None,
    email: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Get reservations with optional filters"""
    reservation_service = ReservationService(db)
    
    if date:
        from datetime import datetime
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        return reservation_service.get_reservations_for_date(target_date, room_id)
    else:
        return reservation_service.search_reservations(
            customer_name=customer_name,
            email=email
        )


@router.get("/reservations/{reservation_id}", response_model=ReservationWithTables)
def get_reservation(
    reservation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Get a specific reservation"""
    reservation_service = ReservationService(db)
    reservation = reservation_service.get_reservation(reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return reservation


@router.put("/reservations/{reservation_id}", response_model=ReservationWithTables)
def update_reservation(
    reservation_id: str,
    update_data: ReservationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Update a reservation"""
    reservation_service = ReservationService(db)
    reservation = reservation_service.update_reservation(reservation_id, update_data)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    return reservation


@router.delete("/reservations/{reservation_id}")
def cancel_reservation(
    reservation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Cancel a reservation"""
    reservation_service = ReservationService(db)
    if reservation_service.cancel_reservation(reservation_id):
        return {"message": "Reservation cancelled successfully"}
    else:
        raise HTTPException(status_code=404, detail="Reservation not found")


# PDF Generation
@router.get("/pdf/daily/{target_date}")
def generate_daily_pdf(
    target_date: str,
    room_id: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Generate daily PDF with reservation slips"""
    from datetime import datetime
    
    try:
        date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    reservation_service = ReservationService(db)
    reservations = reservation_service.get_reservations_for_date(date_obj, room_id)
    
    if not reservations:
        raise HTTPException(status_code=404, detail="No reservations found for this date")
    
    pdf_service = PDFService()
    pdf_bytes = pdf_service.generate_daily_pdf(reservations, date_obj)
    
    filename = f"reservations_{target_date}.pdf"
    if room_id:
        room = db.query(Room).filter(Room.id == room_id).first()
        if room:
            filename = f"reservations_{room.name}_{target_date}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename={filename}.html"}
    )


# User Management (Admin only)
@router.post("/users", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new user (admin only)"""
    from app.core.security import get_password_hash
    
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        password_hash=hashed_password,
        role=user_data.role
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=str(user.id),
        username=user.username,
        role=user.role,
        created_at=user.created_at
    )


@router.get("/users", response_model=List[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get all users (admin only)"""
    users = db.query(User).all()
    return [
        UserResponse(
            id=str(user.id),
            username=user.username,
            role=user.role,
            created_at=user.created_at
        )
        for user in users
    ] 