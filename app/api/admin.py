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
@router.get("/migrate-database") 
def force_database_migration(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Force database migration and create test data - ADMIN ONLY"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Add missing columns to reservations table if they don't exist
        # First, rollback any failed transaction
        db.rollback()
        
        # Check and add reservation_type column
        column_exists = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='reservations' AND column_name='reservation_type'
        """)).fetchone()
        
        if not column_exists:
            try:
                db.execute(text("ALTER TABLE reservations ADD COLUMN reservation_type VARCHAR DEFAULT 'dining'"))
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"Warning: Could not add reservation_type column: {e}")
        
        # Check and add admin_notes column
        admin_notes_exists = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='reservations' AND column_name='admin_notes'
        """)).fetchone()
        
        if not admin_notes_exists:
            try:
                db.execute(text("ALTER TABLE reservations ADD COLUMN admin_notes TEXT"))
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"Warning: Could not add admin_notes column: {e}")
        
        # Update existing reservations to have default reservation_type
        try:
            db.execute(text("UPDATE reservations SET reservation_type = 'dining' WHERE reservation_type IS NULL OR reservation_type = ''"))
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Warning: Could not update reservation_type: {e}")
        
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


@router.delete("/tables/{table_id}")
def delete_table(
    table_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Delete a table"""
    table = db.query(Table).filter(Table.id == table_id).first()
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table not found"
        )
    
    # Check if table has any active reservations
    from app.models.reservation import ReservationTable, ReservationStatus
    active_reservations = db.query(ReservationTable).join(
        Reservation
    ).filter(
        ReservationTable.table_id == table_id,
        Reservation.status == ReservationStatus.CONFIRMED,
        Reservation.date >= date.today()
    ).first()
    
    if active_reservations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete table with active reservations"
        )
    
    db.delete(table)
    db.commit()
    return {"message": "Table deleted successfully"}


@router.post("/setup-tables")
def setup_tables_one_time(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """One-time setup: Create all tables for the 4 rooms"""
    try:
        # Check if tables already exist
        existing_tables = db.query(Table).count()
        if existing_tables > 0:
            return {"message": f"Tables already exist ({existing_tables} found). Skipping setup."}
        
        # Table data for all rooms
        tables_data = [
            # Front Room tables
            {"id": "550e8400-e29b-41d4-a716-446655440101", "room_id": "550e8400-e29b-41d4-a716-446655440001", "name": "F1", "capacity": 4, "combinable": True, "x": 10, "y": 10, "width": 80, "height": 60},
            {"id": "550e8400-e29b-41d4-a716-446655440102", "room_id": "550e8400-e29b-41d4-a716-446655440001", "name": "F2", "capacity": 4, "combinable": True, "x": 100, "y": 10, "width": 80, "height": 60},
            {"id": "550e8400-e29b-41d4-a716-446655440103", "room_id": "550e8400-e29b-41d4-a716-446655440001", "name": "F3", "capacity": 2, "combinable": True, "x": 190, "y": 10, "width": 60, "height": 50},
            {"id": "550e8400-e29b-41d4-a716-446655440104", "room_id": "550e8400-e29b-41d4-a716-446655440001", "name": "F4", "capacity": 6, "combinable": True, "x": 10, "y": 80, "width": 100, "height": 70},
            
            # Middle Room tables
            {"id": "550e8400-e29b-41d4-a716-446655440105", "room_id": "550e8400-e29b-41d4-a716-446655440002", "name": "M1", "capacity": 4, "combinable": True, "x": 10, "y": 10, "width": 80, "height": 60},
            {"id": "550e8400-e29b-41d4-a716-446655440106", "room_id": "550e8400-e29b-41d4-a716-446655440002", "name": "M2", "capacity": 4, "combinable": True, "x": 100, "y": 10, "width": 80, "height": 60},
            {"id": "550e8400-e29b-41d4-a716-446655440107", "room_id": "550e8400-e29b-41d4-a716-446655440002", "name": "M3", "capacity": 6, "combinable": True, "x": 190, "y": 10, "width": 100, "height": 70},
            {"id": "550e8400-e29b-41d4-a716-446655440108", "room_id": "550e8400-e29b-41d4-a716-446655440002", "name": "M4", "capacity": 8, "combinable": True, "x": 10, "y": 80, "width": 120, "height": 80},
            {"id": "550e8400-e29b-41d4-a716-446655440109", "room_id": "550e8400-e29b-41d4-a716-446655440002", "name": "M5", "capacity": 2, "combinable": True, "x": 140, "y": 80, "width": 60, "height": 50},
            {"id": "550e8400-e29b-41d4-a716-446655440110", "room_id": "550e8400-e29b-41d4-a716-446655440002", "name": "M6", "capacity": 2, "combinable": True, "x": 210, "y": 80, "width": 60, "height": 50},
            
            # Back Room tables
            {"id": "550e8400-e29b-41d4-a716-446655440111", "room_id": "550e8400-e29b-41d4-a716-446655440003", "name": "B1", "capacity": 4, "combinable": True, "x": 10, "y": 10, "width": 80, "height": 60},
            {"id": "550e8400-e29b-41d4-a716-446655440112", "room_id": "550e8400-e29b-41d4-a716-446655440003", "name": "B2", "capacity": 6, "combinable": True, "x": 100, "y": 10, "width": 100, "height": 70},
            {"id": "550e8400-e29b-41d4-a716-446655440113", "room_id": "550e8400-e29b-41d4-a716-446655440003", "name": "B3", "capacity": 8, "combinable": True, "x": 10, "y": 80, "width": 120, "height": 80},
            {"id": "550e8400-e29b-41d4-a716-446655440114", "room_id": "550e8400-e29b-41d4-a716-446655440003", "name": "B4", "capacity": 10, "combinable": False, "x": 140, "y": 10, "width": 150, "height": 120},
            
            # Biergarten tables
            {"id": "550e8400-e29b-41d4-a716-446655440115", "room_id": "550e8400-e29b-41d4-a716-446655440004", "name": "BG1", "capacity": 6, "combinable": True, "x": 10, "y": 10, "width": 100, "height": 70},
            {"id": "550e8400-e29b-41d4-a716-446655440116", "room_id": "550e8400-e29b-41d4-a716-446655440004", "name": "BG2", "capacity": 6, "combinable": True, "x": 120, "y": 10, "width": 100, "height": 70},
            {"id": "550e8400-e29b-41d4-a716-446655440117", "room_id": "550e8400-e29b-41d4-a716-446655440004", "name": "BG3", "capacity": 8, "combinable": True, "x": 230, "y": 10, "width": 120, "height": 80},
            {"id": "550e8400-e29b-41d4-a716-446655440118", "room_id": "550e8400-e29b-41d4-a716-446655440004", "name": "BG4", "capacity": 8, "combinable": True, "x": 10, "y": 90, "width": 120, "height": 80},
            {"id": "550e8400-e29b-41d4-a716-446655440119", "room_id": "550e8400-e29b-41d4-a716-446655440004", "name": "BG5", "capacity": 10, "combinable": True, "x": 140, "y": 90, "width": 150, "height": 90},
            {"id": "550e8400-e29b-41d4-a716-446655440120", "room_id": "550e8400-e29b-41d4-a716-446655440004", "name": "BG6", "capacity": 12, "combinable": False, "x": 300, "y": 90, "width": 180, "height": 100}
        ]
        
        # Create all tables
        tables_created = []
        for table_data in tables_data:
            table = Table(**table_data)
            db.add(table)
            tables_created.append(f"{table_data['name']} (capacity: {table_data['capacity']})")
        
        # Fix reservation_type column if missing
        try:
            # Check if column exists by trying to query it
            db.execute(text("SELECT reservation_type FROM reservations LIMIT 1"))
        except Exception:
            # Column doesn't exist, add it
            db.execute(text("""
                DO $$ BEGIN
                    CREATE TYPE reservationtype AS ENUM (
                        'dining', 'fun', 'team_event', 'birthday', 'party', 'special_event'
                    );
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """))
            db.execute(text("""
                ALTER TABLE reservations 
                ADD COLUMN reservation_type reservationtype 
                DEFAULT 'dining' NOT NULL
            """))
        
        db.commit()
        
        return {
            "message": f"Successfully created {len(tables_created)} tables!",
            "tables_created": tables_created,
            "rooms_setup": {
                "Front Room": "F1, F2, F3, F4 (2-6 people)",
                "Middle Room": "M1, M2, M3, M4, M5, M6 (2-8 people)", 
                "Back Room": "B1, B2, B3, B4 (4-10 people)",
                "Biergarten": "BG1, BG2, BG3, BG4, BG5, BG6 (6-12 people)"
            },
            "reservation_type_column": "Fixed/Added"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting up tables: {str(e)}"
        )


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
    
    # Order by date and time (earliest first)
    reservations = query.order_by(Reservation.date, Reservation.time).all()
    
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
    """Get a specific reservation by ID"""
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
    reservation_data: ReservationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Update a specific reservation"""
    reservation_service = ReservationService(db)
    
    try:
        reservation = reservation_service.update_reservation(reservation_id, reservation_data)
        return reservation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


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


@router.put("/reservations/{reservation_id}/tables")
def update_reservation_tables(
    reservation_id: str,
    table_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff_user)
):
    """Update table assignments for a reservation"""
    from app.services.table_service import TableService
    
    # Get the reservation
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    table_ids = table_data.get('table_ids', [])
    if not table_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one table must be selected"
        )
    
    # Verify all tables exist and are in the same room
    tables = db.query(Table).filter(Table.id.in_(table_ids)).all()
    if len(tables) != len(table_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more table IDs are invalid"
        )
    
    # Check if all tables are in the same room
    room_ids = set(table.room_id for table in tables)
    if len(room_ids) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All tables must be in the same room"
        )
    
    # Check table availability (exclude current reservation)
    table_service = TableService(db)
    reserved_table_ids = table_service.get_reserved_table_ids(
        reservation.date, 
        reservation.time,
        exclude_reservation_id=reservation_id
    )
    
    conflicting_tables = set(table_ids) & set(reserved_table_ids)
    if conflicting_tables:
        conflicting_names = [t.name for t in tables if str(t.id) in conflicting_tables]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tables {', '.join(conflicting_names)} are already reserved at this time"
        )
    
    # Update table assignments
    table_service.assign_tables_to_reservation(reservation_id, table_ids)
    
    # Update reservation room if needed
    new_room_id = tables[0].room_id
    if reservation.room_id != new_room_id:
        reservation.room_id = new_room_id
        db.commit()
    
    return {"message": "Table assignment updated successfully"}


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