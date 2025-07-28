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
from app.models.reservation import Reservation, ReservationStatus, ReservationType, DashboardNote
from app.models.settings import WorkingHours, DayOfWeek, RestaurantSettings
from app.api.deps import get_current_staff_user, get_current_admin_user
from app.core.database import Base, engine
from datetime import date, time, datetime, timedelta
from sqlalchemy import text
import uuid
import random

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/migrate-database")
def force_database_migration(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Force database migration and create test data - ADMIN ONLY"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Add missing columns to reservations table if they don't exist
        try:
            db.execute(text("SELECT reservation_type FROM reservations LIMIT 1"))
        except Exception:
            db.execute(text("ALTER TABLE reservations ADD COLUMN reservation_type VARCHAR DEFAULT 'dining'"))
            db.commit()
        
        try:
            db.execute(text("SELECT admin_notes FROM reservations LIMIT 1"))
        except Exception:
            db.execute(text("ALTER TABLE reservations ADD COLUMN admin_notes TEXT"))
            db.commit()
        
        # Update existing reservations to have default reservation_type
        try:
            db.execute(text("UPDATE reservations SET reservation_type = 'dining' WHERE reservation_type IS NULL"))
            db.commit()
        except Exception:
            pass
        
        # Seed test data if no reservations exist
        reservation_count = db.query(Reservation).count()
        if reservation_count == 0:
            # Get rooms for test data
            rooms = db.query(Room).all()
            if rooms:
                # Test customers
                test_customers = [
                    {"name": "Emma Thompson", "email": "emma.thompson@email.com", "phone": "+49 30 12345671"},
                    {"name": "James Wilson", "email": "james.wilson@email.com", "phone": "+49 30 12345672"},
                    {"name": "Sophie Mueller", "email": "sophie.mueller@email.com", "phone": "+49 30 12345673"},
                    {"name": "Michael Brown", "email": "michael.brown@email.com", "phone": "+49 30 12345674"},
                    {"name": "Anna Schmidt", "email": "anna.schmidt@email.com", "phone": "+49 30 12345675"},
                    {"name": "David Johnson", "email": "david.johnson@email.com", "phone": "+49 30 12345676"},
                    {"name": "Lisa Weber", "email": "lisa.weber@email.com", "phone": "+49 30 12345677"},
                    {"name": "Robert Davis", "email": "robert.davis@email.com", "phone": "+49 30 12345678"},
                    {"name": "Maria Garcia", "email": "maria.garcia@email.com", "phone": "+49 30 12345679"},
                    {"name": "Thomas Klein", "email": "thomas.klein@email.com", "phone": "+49 30 12345680"}
                ]
                
                customer_notes = [
                    "Celebrating our anniversary!",
                    "Please prepare a birthday cake",
                    "Team building dinner for 8 people",
                    "Vegetarian options needed",
                    "Window table preferred",
                    "Birthday surprise for my daughter",
                    "Business meeting - quiet table please"
                ]
                
                admin_notes = [
                    "VIP customer - special attention",
                    "Regular customer - knows preferences", 
                    "Large group - coordinate service",
                    "Special dietary requirements noted"
                ]
                
                today = date.today()
                
                # Create past reservations for history
                for i in range(15):
                    past_date = today - timedelta(days=random.randint(1, 30))
                    customer = random.choice(test_customers)
                    
                    reservation = Reservation(
                        customer_name=customer["name"],
                        email=customer["email"],
                        phone=customer["phone"],
                        party_size=random.randint(2, 8),
                        date=past_date,
                        time=time(hour=random.randint(12, 21), minute=random.choice([0, 30])),
                        room_id=random.choice(rooms).id,
                        reservation_type=random.choice(list(ReservationType)),
                        status=ReservationStatus.CONFIRMED,
                        notes=random.choice(customer_notes) if random.random() > 0.4 else None,
                        admin_notes=random.choice(admin_notes) if random.random() > 0.6 else None
                    )
                    db.add(reservation)
                
                # Create future reservations
                for day_offset in range(7):
                    reservation_date = today + timedelta(days=day_offset)
                    daily_reservations = random.randint(2, 5)
                    
                    for _ in range(daily_reservations):
                        customer = random.choice(test_customers)
                        
                        reservation = Reservation(
                            customer_name=customer["name"],
                            email=customer["email"],
                            phone=customer["phone"],
                            party_size=random.randint(2, 10),
                            date=reservation_date,
                            time=time(hour=random.randint(12, 21), minute=random.choice([0, 30])),
                            room_id=random.choice(rooms).id,
                            reservation_type=random.choice(list(ReservationType)),
                            status=ReservationStatus.CONFIRMED,
                            notes=random.choice(customer_notes) if random.random() > 0.4 else None,
                            admin_notes=random.choice(admin_notes) if random.random() > 0.6 else None
                        )
                        db.add(reservation)
        
        # Create dashboard notes if none exist
        note_count = db.query(DashboardNote).count()
        if note_count == 0:
            dashboard_notes = [
                {
                    "title": "Welcome to The Castle Pub!",
                    "content": "Your restaurant management system is now active. All features are working correctly.",
                    "priority": "normal",
                    "author": "admin"
                },
                {
                    "title": "Staff Meeting Reminder",
                    "content": "Don't forget the weekly staff meeting to discuss service improvements.",
                    "priority": "high",
                    "author": "admin"
                },
                {
                    "title": "Special Event Planning",
                    "content": "Planning for upcoming events and special occasions.",
                    "priority": "normal",
                    "author": "admin"
                }
            ]
            
            for note_data in dashboard_notes:
                note = DashboardNote(**note_data)
                db.add(note)
        
        # Create default working hours if none exist
        working_hours_count = db.query(WorkingHours).count()
        if working_hours_count == 0:
            for day in DayOfWeek:
                working_hours = WorkingHours(
                    day_of_week=day,
                    is_open=True,
                    open_time=time(11, 0),
                    close_time=time(23, 0)
                )
                db.add(working_hours)
        
        db.commit()
        
        return {
            "message": "Database migration completed successfully",
            "tables_created": True,
            "test_data_seeded": True,
            "status": "success"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}"
        )


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
    rooms = db.query(Room).filter(Room.active == True).all()
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    if room_data.name is not None:
        room.name = room_data.name
    if room_data.description is not None:
        room.description = room_data.description
    if room_data.active is not None:
        room.active = room_data.active
    
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
        combinable=table_data.combinable
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
    query = db.query(Table).filter(Table.active == True)
    if room_id:
        query = query.filter(Table.room_id == room_id)
    
    tables = query.all()
    return tables


@router.get("/tables/{table_id}", response_model=TableResponse)
def get_table(
    table_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Get a specific table"""
    table = db.query(Table).filter(Table.id == table_id).first()
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found"
        )
    return table


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found"
        )
    
    if table_data.name is not None:
        table.name = table_data.name
    if table_data.capacity is not None:
        table.capacity = table_data.capacity
    if table_data.combinable is not None:
        table.combinable = table_data.combinable
    if table_data.active is not None:
        table.active = table_data.active
    
    db.commit()
    db.refresh(table)
    return table


# Reservation Management
@router.get("/reservations", response_model=List[ReservationWithTables])
def get_reservations(
    date_filter: date = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Get reservations, optionally filtered by date"""
    reservation_service = ReservationService(db)
    
    query = db.query(Reservation)
    if date_filter:
        query = query.filter(Reservation.date == date_filter)
    
    reservations = query.all()
    
    # Convert to ReservationWithTables format
    result = []
    for reservation in reservations:
        reservation_with_tables = reservation_service.get_reservation(str(reservation.id))
        if reservation_with_tables:
            result.append(reservation_with_tables)
    
    return result


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )


# Reports
@router.get("/reports/daily")
def get_daily_report(
    report_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Generate daily report"""
    try:
        pdf_service = PDFService()
        pdf_content = pdf_service.generate_daily_report(report_date)
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=daily_report_{report_date}.pdf"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )


# User Management (Admin only)
@router.post("/users", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new user (Admin only)"""
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    from app.core.security import get_password_hash
    
    user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
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
    """Get all users (Admin only)"""
    users = db.query(User).all()
    
    return [
        UserResponse(
            id=str(user.id),
            username=user.username,
            role=user.role,
            created_at=user.created_at
        ) for user in users
    ] 