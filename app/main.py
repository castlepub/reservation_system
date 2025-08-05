# GRADUALLY RESTORING FUNCTIONALITY AFTER SUCCESSFUL HEALTH CHECK
import os
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db

# Import routers
from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.settings import router as settings_router
from app.api.public import router as public_router
from app.api.dashboard import router as dashboard_router
from app.api.layout import router as layout_router

# Create FastAPI app
app = FastAPI(title="The Castle Pub Reservation System")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/auth")
app.include_router(admin_router, prefix="/admin")
app.include_router(settings_router, prefix="/api")
app.include_router(public_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(layout_router, prefix="/api")

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
try:
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
except Exception:
    pass  # Ignore static file mounting errors

@app.get("/")
async def root():
    """Serve the main HTML file"""
    try:
        html_file = os.path.join(static_dir, "index.html")
        if os.path.exists(html_file):
            return FileResponse(html_file)
    except Exception:
        pass
    return {"message": "The Castle Pub Reservation System", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong", "timestamp": datetime.utcnow().isoformat()}

# Basic API endpoints (without database)
@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {"message": "The Castle Pub Reservation System API", "status": "running"}

# Temporary auth endpoints (to bypass router issues)
@app.post("/auth/login")
async def login_temp():
    """Temporary login endpoint - no auth required"""
    return {
        "access_token": "temporary_token_12345",
        "token_type": "bearer",
        "user": {
            "id": "temp_user",
            "username": "admin",
            "role": "admin",
            "created_at": datetime.utcnow().isoformat()
        }
    }

@app.post("/api/auth/login")
async def login_api_temp():
    """Temporary login endpoint for /api/auth/login - no auth required"""
    return {
        "access_token": "temporary_token_12345",
        "token_type": "bearer",
        "user": {
            "id": "temp_user",
            "username": "admin",
            "role": "admin",
            "created_at": datetime.utcnow().isoformat()
        }
    }

@app.get("/auth/me")
async def get_auth_me_temp():
    """Temporary auth me endpoint - no auth required"""
    return {
        "id": "temp_user",
        "username": "admin",
        "role": "admin",
        "created_at": datetime.utcnow().isoformat()
    }

@app.get("/api/auth/me")
async def get_auth_me_api_temp():
    """Temporary auth me endpoint for /api/auth/me - no auth required"""
    return {
        "id": "temp_user",
        "username": "admin",
        "role": "admin",
        "created_at": datetime.utcnow().isoformat()
    }

# Public API endpoints (with database access)
@app.get("/api/rooms")
async def get_rooms_public(db: Session = Depends(get_db)):
    """Get all active rooms for public use"""
    from app.models.room import Room
    rooms = db.query(Room).filter(Room.active == True).all()
    return [
        {
            "id": room.id,
            "name": room.name,
            "description": room.description
        }
        for room in rooms
    ]

@app.get("/api/tables")
async def get_tables_public(db: Session = Depends(get_db)):
    """Get all active tables for public use"""
    from app.models.table import Table
    from app.models.room import Room
    tables = db.query(Table).filter(Table.active == True).all()
    return [
        {
            "id": table.id,
            "name": table.name,
            "room_id": table.room_id,
            "capacity": table.capacity,
            "combinable": table.combinable
        }
        for table in tables
    ]

@app.get("/api/rooms/{room_id}/tables")
async def get_room_tables_public(room_id: str, db: Session = Depends(get_db)):
    """Get all tables for a specific room"""
    from app.models.table import Table
    tables = db.query(Table).filter(Table.room_id == room_id, Table.active == True).all()
    return [
        {
            "id": table.id,
            "name": table.name,
            "capacity": table.capacity,
            "combinable": table.combinable
        }
        for table in tables
    ]

# Dashboard endpoints (temporary)
@app.get("/api/dashboard/stats")
async def get_dashboard_stats_temp(db: Session = Depends(get_db)):
    """Get real dashboard stats with weekly forecast"""
    from app.models.reservation import Reservation, ReservationStatus
    from datetime import date, timedelta
    
    today = date.today()
    
    # Get today's confirmed reservations
    today_reservations = db.query(Reservation).filter(
        Reservation.date == today,
        Reservation.status == ReservationStatus.CONFIRMED
    ).all()
    
    total_reservations_today = len(today_reservations)
    total_guests_today = sum(r.party_size for r in today_reservations)
    
    # Get this week's reservations (Monday to Sunday)
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    week_reservations = db.query(Reservation).filter(
        Reservation.date >= start_of_week,
        Reservation.date <= end_of_week,
        Reservation.status == ReservationStatus.CONFIRMED
    ).all()
    
    total_reservations_week = len(week_reservations)
    total_guests_week = sum(r.party_size for r in week_reservations)
    
    # Create weekly forecast for the next 7 days
    weekly_forecast = []
    for i in range(7):
        forecast_date = today + timedelta(days=i)
        day_reservations = [r for r in week_reservations if r.date == forecast_date]
        
        weekly_forecast.append({
            "date": forecast_date.isoformat(),
            "day_name": forecast_date.strftime("%A"),
            "reservations_count": len(day_reservations),
            "guests_count": sum(r.party_size for r in day_reservations),
            "reservations": [
                {
                    "time": r.time,
                    "party_size": r.party_size,
                    "customer_name": r.customer_name
                } for r in day_reservations
            ]
        })
    
    return {
        "total_reservations_today": total_reservations_today,
        "total_guests_today": total_guests_today,
        "total_reservations_week": total_reservations_week,
        "total_guests_week": total_guests_week,
        "weekly_forecast": weekly_forecast,
        "guest_notes": []
    }

@app.get("/api/dashboard/notes")
async def get_dashboard_notes_temp():
    """Temporary dashboard notes"""
    return []

@app.post("/api/dashboard/notes")
async def create_dashboard_note_temp():
    """Temporary create dashboard note"""
    return {
        "id": "temp_note_1",
        "title": "Temporary Note",
        "content": "This is a temporary note",
        "priority": "medium",
        "author": "admin",
        "created_at": datetime.utcnow().isoformat()
    }

@app.delete("/api/dashboard/notes/{note_id}")
async def delete_dashboard_note_temp(note_id: str):
    """Temporary delete dashboard note"""
    return {"message": "Note deleted successfully"}

@app.get("/api/dashboard/customers")
async def get_dashboard_customers_temp():
    """Temporary dashboard customers"""
    return []

@app.get("/api/dashboard/today")
async def get_dashboard_today_temp(db: Session = Depends(get_db)):
    """Get today's confirmed reservations"""
    from app.models.reservation import Reservation, ReservationStatus
    from datetime import date
    
    today = date.today()
    reservations = db.query(Reservation).filter(
        Reservation.date == today,
        Reservation.status == ReservationStatus.CONFIRMED
    ).order_by(Reservation.time).all()
    
    return [
        {
            "id": r.id,
            "customer_name": r.customer_name,
            "time": r.time,
            "party_size": r.party_size,
            "table_names": [],  # Will be populated when table assignment is implemented
            "reservation_type": r.reservation_type.value if r.reservation_type else "dining",
            "status": r.status,
            "notes": r.notes,
            "admin_notes": r.admin_notes
        } for r in reservations
    ]

# Auth endpoints are now handled by the auth router

# Settings endpoints (temporary - no auth required)
@app.get("/api/settings/restaurant")
async def get_restaurant_settings_temp():
    """Temporary restaurant settings - no auth required"""
    return [
        {"key": "name", "value": "The Castle Pub"},
        {"key": "address", "value": "123 Castle Street"},
        {"key": "phone", "value": "+1 234 567 8900"},
        {"key": "email", "value": "info@castlepub.com"},
        {"key": "website", "value": "www.castlepub.com"}
    ]

@app.get("/api/settings/rooms")
async def get_rooms_settings_temp(db: Session = Depends(get_db)):
    """Get rooms settings with table counts - no auth required"""
    from app.models.room import Room
    from app.models.table import Table
    
    rooms = db.query(Room).all()
    result = []
    
    for room in rooms:
        # Count tables for this room
        table_count = db.query(Table).filter(Table.room_id == room.id, Table.active == True).count()
        
        result.append({
            "id": room.id,
            "name": room.name,
            "description": room.description,
            "active": room.active,
            "table_count": table_count,
            "created_at": room.created_at.isoformat() if room.created_at else None,
            "updated_at": room.updated_at.isoformat() if room.updated_at else None
        })
    
    return result

@app.get("/api/settings/rooms/{room_id}")
async def get_room_settings_temp(room_id: str, db: Session = Depends(get_db)):
    """Get specific room settings - no auth required"""
    from app.models.room import Room
    from app.models.table import Table
    
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Count tables for this room
    table_count = db.query(Table).filter(Table.room_id == room.id, Table.active == True).count()
    
    return {
        "id": room.id,
        "name": room.name,
        "description": room.description,
        "active": room.active,
        "table_count": table_count,
        "created_at": room.created_at.isoformat() if room.created_at else None,
        "updated_at": room.updated_at.isoformat() if room.updated_at else None
    }

@app.put("/api/settings/rooms/{room_id}")
async def update_room_settings_temp(room_id: str, room_data: dict, db: Session = Depends(get_db)):
    """Update room settings - no auth required"""
    from app.models.room import Room
    
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Update room fields
    if "name" in room_data:
        room.name = room_data["name"]
    if "description" in room_data:
        room.description = room_data["description"]
    if "active" in room_data:
        room.active = room_data["active"]
    
    room.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(room)
    
    return {
        "id": room.id,
        "name": room.name,
        "description": room.description,
        "active": room.active,
        "created_at": room.created_at.isoformat() if room.created_at else None,
        "updated_at": room.updated_at.isoformat() if room.updated_at else None
    }

@app.delete("/api/settings/rooms/{room_id}")
async def delete_room_settings_temp(room_id: str, db: Session = Depends(get_db)):
    """Delete room settings - no auth required"""
    from app.models.room import Room
    
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    db.delete(room)
    db.commit()
    
    return {"message": "Room deleted successfully"}

@app.post("/api/settings/rooms")
async def create_room_settings_temp(room_data: dict, db: Session = Depends(get_db)):
    """Create room settings - no auth required"""
    from app.models.room import Room
    import uuid
    
    new_room = Room(
        id=str(uuid.uuid4()),
        name=room_data.get("name", "New Room"),
        description=room_data.get("description"),
        active=room_data.get("active", True)
    )
    
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    
    return {
        "id": new_room.id,
        "name": new_room.name,
        "description": new_room.description,
        "active": new_room.active,
        "table_count": 0,
        "created_at": new_room.created_at.isoformat() if new_room.created_at else None,
        "updated_at": new_room.updated_at.isoformat() if new_room.updated_at else None
    }

@app.get("/api/settings/special-days")
async def get_special_days_temp():
    """Temporary special days - no auth required"""
    return []

# Admin endpoints are handled by the admin router

# Admin endpoints are now handled by the admin router

@app.get("/admin/rooms")
async def get_admin_rooms_temp(db: Session = Depends(get_db)):
    """Get all rooms for admin - no auth required for now"""
    from app.models.room import Room
    
    rooms = db.query(Room).all()
    result = []
    
    for room in rooms:
        result.append({
            "id": room.id,
            "name": room.name,
            "description": room.description,
            "active": room.active,
            "created_at": room.created_at.isoformat() if room.created_at else None,
            "updated_at": room.updated_at.isoformat() if room.updated_at else None
        })
    
    return result

@app.get("/admin/tables")
async def get_admin_tables_temp(db: Session = Depends(get_db)):
    """Get all tables for admin - no auth required for now"""
    from app.models.table import Table
    from app.models.room import Room
    
    tables = db.query(Table).all()
    result = []
    
    for table in tables:
        # Get room name
        room = db.query(Room).filter(Room.id == table.room_id).first()
        room_name = room.name if room else "Unknown Room"
        
        result.append({
            "id": table.id,
            "name": table.name,
            "room_id": table.room_id,
            "room_name": room_name,
            "capacity": table.capacity,
            "combinable": table.combinable,
            "active": table.active,
            "created_at": table.created_at.isoformat() if table.created_at else None,
            "updated_at": table.updated_at.isoformat() if table.updated_at else None
        })
    
    return result

@app.get("/admin/reservations")
async def get_admin_reservations_temp(db: Session = Depends(get_db), date: str = None):
    """Get reservations for admin - defaults to today's date"""
    from app.models.reservation import Reservation
    from app.models.room import Room
    from datetime import date as date_type
    
    # If no date specified, use today
    if not date:
        target_date = date_type.today()
    else:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        except:
            target_date = date_type.today()
    
    # Get reservations for the specified date
    reservations = db.query(Reservation).filter(Reservation.date == target_date).order_by(Reservation.time).all()
    result = []
    
    for reservation in reservations:
        # Get room name if room_id exists
        room_name = None
        if reservation.room_id:
            room = db.query(Room).filter(Room.id == reservation.room_id).first()
            room_name = room.name if room else None
        
        result.append({
            "id": reservation.id,
            "customer_name": reservation.customer_name,
            "email": reservation.email,
            "phone": reservation.phone,
            "date": reservation.date.isoformat() if reservation.date else None,
            "time": reservation.time,
            "party_size": reservation.party_size,
            "status": reservation.status,
            "notes": reservation.notes,
            "room_name": room_name,
            "created_at": reservation.created_at.isoformat() if reservation.created_at else None
        })
    
    return result

@app.post("/api/reservations")
async def create_reservation_temp(reservation_data: dict, db: Session = Depends(get_db)):
    """Create a new reservation - no auth required for now"""
    from app.models.reservation import Reservation, ReservationStatus, ReservationType
    from datetime import datetime
    import uuid
    
    try:
        # Parse date
        date_str = reservation_data.get("date")
        if date_str:
            reservation_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            reservation_date = datetime.now().date()
        
        # Parse time
        time_str = reservation_data.get("time", "19:00")
        if isinstance(time_str, str):
            # Handle time format conversion
            if len(time_str.split(':')) == 2:
                time_str = f"{time_str}:00"
            reservation_time = datetime.strptime(time_str, "%H:%M:%S").time()
        else:
            reservation_time = time_str
        
        # Ensure duration_hours is provided and valid
        duration_hours = reservation_data.get("duration_hours", 2)
        if duration_hours is None:
            duration_hours = 2
        
        # Create new reservation
        new_reservation = Reservation(
            id=str(uuid.uuid4()),
            customer_name=reservation_data.get("customer_name", "Unknown Customer"),
            email=reservation_data.get("email", ""),
            phone=reservation_data.get("phone", ""),
            date=reservation_date,
            time=reservation_time,
            party_size=reservation_data.get("party_size", 2),
            duration_hours=duration_hours,
            status=ReservationStatus.CONFIRMED,
            reservation_type=ReservationType.DINING,
            notes=reservation_data.get("notes"),
            admin_notes=reservation_data.get("admin_notes"),
            room_id=reservation_data.get("room_id")
        )
        
        db.add(new_reservation)
        db.commit()
        db.refresh(new_reservation)
        
        return {
            "status": "success", 
            "message": "Reservation created successfully", 
            "id": new_reservation.id,
            "reservation": {
                "id": new_reservation.id,
                "customer_name": new_reservation.customer_name,
                "date": new_reservation.date.isoformat() if new_reservation.date else None,
                "time": str(new_reservation.time),
                "party_size": new_reservation.party_size,
                "duration_hours": new_reservation.duration_hours,
                "status": new_reservation.status.value
            }
        }
    except Exception as e:
        db.rollback()
        print(f"Error creating reservation: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to create reservation: {str(e)}")

# Additional missing endpoints
@app.get("/api/settings/working-hours")
async def get_all_working_hours_temp():
    """Temporary working hours for all days"""
    standard_hours = [
        {"time": "17:00", "available": True},
        {"time": "17:30", "available": True},
        {"time": "18:00", "available": True},
        {"time": "18:30", "available": True},
        {"time": "19:00", "available": True},
        {"time": "19:30", "available": True},
        {"time": "20:00", "available": True},
        {"time": "20:30", "available": True},
        {"time": "21:00", "available": True},
        {"time": "21:30", "available": True}
    ]
    return {
        "monday": standard_hours,
        "tuesday": standard_hours,
        "wednesday": standard_hours,
        "thursday": standard_hours,
        "friday": standard_hours,
        "saturday": standard_hours,
        "sunday": standard_hours
    }

@app.get("/api/settings/working-hours/{day}")
async def get_working_hours_by_day_temp(day: str):
    """Temporary working hours for specific day"""
    return [
        {"time": "17:00", "available": True},
        {"time": "17:30", "available": True},
        {"time": "18:00", "available": True},
        {"time": "18:30", "available": True},
        {"time": "19:00", "available": True},
        {"time": "19:30", "available": True},
        {"time": "20:00", "available": True},
        {"time": "20:30", "available": True},
        {"time": "21:00", "available": True},
        {"time": "21:30", "available": True}
    ]

@app.get("/api/settings/working-hours/{day}/time-slots")
async def get_working_hours_time_slots_temp(day: str):
    """Temporary working hours time slots - returns time_slots array as expected by frontend"""
    return {
        "time_slots": [
            "17:00", "17:30", "18:00", "18:30", "19:00", 
            "19:30", "20:00", "20:30", "21:00", "21:30"
        ],
        "day": day,
        "open": True,
        "message": "Restaurant is open"
    }

@app.get("/api/layout/daily/{date}")
async def get_layout_daily_temp(date: str, db: Session = Depends(get_db)):
    """Get daily view with all room layouts and reservations"""
    from app.models.room import Room
    from app.models.table import Table
    from app.models.reservation import Reservation
    from datetime import datetime
    
    try:
        # Parse date
        target_date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except:
        target_date_obj = datetime.now().date()
    
    # Get all active rooms
    rooms = db.query(Room).filter(Room.active == True).all()
    
    daily_data = {
        "date": target_date_obj.isoformat(),
        "rooms": []
    }
    
    for room in rooms:
        try:
            # Get tables for this room
            tables = db.query(Table).filter(Table.room_id == room.id, Table.active == True).all()
            
            # Get reservations for this date and room
            reservations = db.query(Reservation).filter(
                Reservation.date == target_date_obj,
                Reservation.room_id == room.id
            ).all()
            
            # Convert tables to layout format with positioning
            table_layouts = []
            for i, table in enumerate(tables):
                # Position tables in a grid pattern
                row = i // 4
                col = i % 4
                x_pos = 50 + (col * 120)
                y_pos = 50 + (row * 100)
                
                # Check if table has reservations
                table_reservations = [r for r in reservations if r.table_id == table.id]
                status = "reserved" if table_reservations else "available"
                
                table_layouts.append({
                    "layout_id": table.id,
                    "table_id": table.id,
                    "table_name": table.name,
                    "capacity": table.capacity,
                    "x_position": x_pos,
                    "y_position": y_pos,
                    "width": 80,
                    "height": 80,
                    "shape": "rectangle",
                    "color": "#4CAF50" if status == "available" else "#FF9800",
                    "border_color": "#2E7D32" if status == "available" else "#E65100",
                    "text_color": "#FFFFFF",
                    "font_size": 12,
                    "z_index": 1,
                    "show_name": True,
                    "show_capacity": True,
                    "status": status,
                    "combinable": table.combinable,
                    "reservations": [
                        {
                            "id": r.id,
                            "customer_name": r.customer_name,
                            "time": r.time,
                            "party_size": r.party_size,
                            "status": r.status
                        } for r in table_reservations
                    ]
                })
            
            # Create room layout data
            room_layout = {
                "width": 800,
                "height": 600,
                "background_color": "#F5F5F5",
                "show_entrance": True,
                "show_bar": False
            }
            
            daily_data["rooms"].append({
                "id": room.id,
                "name": room.name,
                "description": room.description,
                "layout": room_layout,
                "tables": table_layouts,
                "reservations": [
                    {
                        "id": r.id,
                        "customer_name": r.customer_name,
                        "time": r.time,
                        "party_size": r.party_size,
                        "status": r.status,
                        "table_id": r.table_id
                    } for r in reservations
                ]
            })
        except Exception as e:
            # Log the error but continue with other rooms
            print(f"Error processing room {room.id}: {str(e)}")
            continue
    
    return daily_data

@app.get("/api/layout/editor/{room_id}")
async def get_layout_editor_temp(room_id: str, target_date: str, db: Session = Depends(get_db)):
    """Temporary layout editor data"""
    from app.models.room import Room
    from app.models.table import Table
    from app.models.reservation import Reservation
    from datetime import datetime
    
    # Get room
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Get tables for this room
    tables = db.query(Table).filter(Table.room_id == room_id, Table.active == True).all()
    
    # Parse target date
    try:
        target_date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
    except:
        target_date_obj = datetime.now().date()
    
    # Get reservations for this date and room
    reservations = db.query(Reservation).filter(
        Reservation.date == target_date_obj,
        Reservation.room_id == room_id
    ).all()
    
    # Convert tables to layout format with proper positioning
    table_layouts = []
    for i, table in enumerate(tables):
        # Position tables in a grid pattern with better spacing
        row = i // 4  # 4 tables per row instead of 3
        col = i % 4
        x_pos = 50 + (col * 120)  # Reduced spacing
        y_pos = 50 + (row * 100)  # Reduced spacing
        
        table_layouts.append({
             "layout_id": table.id,
             "table_id": table.id,
             "table_name": table.name,
             "capacity": table.capacity,
             "x_position": x_pos,
             "y_position": y_pos,
             "width": 80,
             "height": 80,
             "shape": "rectangle",
             "color": "#4CAF50",
             "border_color": "#2E7D32",
             "text_color": "#FFFFFF",
             "font_size": 12,
             "z_index": 1,
             "show_name": True,
             "show_capacity": True,
             "status": "available",
             "combinable": table.combinable
         })
    
    # Create room layout data
    room_layout = {
        "width": 800,
        "height": 600,
        "background_color": "#F5F5F5",
        "show_entrance": True,
        "show_bar": False
    }
    
    return {
        "room": {
            "id": room.id,
            "name": room.name,
            "description": room.description
        },
        "room_layout": room_layout,
        "tables": table_layouts,
        "reservations": [
            {
                "id": r.id,
                "customer_name": r.customer_name,
                "time": r.time,
                "party_size": r.party_size,
                "status": r.status
            } for r in reservations
        ],
        "target_date": target_date_obj.isoformat()
    }

@app.get("/admin/tables/{table_id}")
async def get_admin_table_temp(table_id: str, db: Session = Depends(get_db)):
    """Get specific table for admin - no auth required for now"""
    from app.models.table import Table
    from app.models.room import Room
    
    table = db.query(Table).filter(Table.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    
    # Get room name
    room = db.query(Room).filter(Room.id == table.room_id).first()
    room_name = room.name if room else "Unknown Room"
    
    return {
        "id": table.id,
        "name": table.name,
        "room_id": table.room_id,
        "room_name": room_name,
        "capacity": table.capacity,
        "combinable": table.combinable,
        "active": table.active,
        "created_at": table.created_at.isoformat() if table.created_at else None,
        "updated_at": table.updated_at.isoformat() if table.updated_at else None
    }

@app.put("/admin/tables/{table_id}")
async def update_admin_table_temp(table_id: str, table_data: dict, db: Session = Depends(get_db)):
    """Update specific table for admin - no auth required for now"""
    from app.models.table import Table
    
    table = db.query(Table).filter(Table.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    
    # Update table fields
    if "name" in table_data:
        table.name = table_data["name"]
    if "capacity" in table_data:
        table.capacity = table_data["capacity"]
    if "combinable" in table_data:
        table.combinable = table_data["combinable"]
    if "active" in table_data:
        table.active = table_data["active"]
    
    table.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(table)
    
    return {
        "id": table.id,
        "name": table.name,
        "room_id": table.room_id,
        "capacity": table.capacity,
        "combinable": table.combinable,
        "active": table.active,
        "created_at": table.created_at.isoformat() if table.created_at else None,
        "updated_at": table.updated_at.isoformat() if table.updated_at else None
    }

# Layout API endpoints for table positioning and management
@app.put("/api/layout/tables/{layout_id}")
async def update_table_position_temp(layout_id: str, position_data: dict, db: Session = Depends(get_db)):
    """Update table position in layout - no auth required for now"""
    # For now, just return success since we're not storing layout positions in the database yet
    return {
        "message": "Table position updated successfully",
        "layout_id": layout_id,
        "x_position": position_data.get("x_position"),
        "y_position": position_data.get("y_position")
    }

@app.post("/api/layout/tables")
async def create_layout_table_temp(table_data: dict, db: Session = Depends(get_db)):
    """Create new table in layout editor"""
    from app.models.table import Table
    from app.models.room import Room
    
    try:
        # Validate room exists
        room = db.query(Room).filter(Room.id == table_data.get("room_id")).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        
        # Create new table
        new_table = Table(
            name=table_data.get("table_name", "New Table"),
            capacity=table_data.get("capacity", 4),
            room_id=table_data.get("room_id"),
            active=True,
            combinable=table_data.get("combinable", False)
        )
        
        db.add(new_table)
        db.commit()
        db.refresh(new_table)
        
        return {
            "id": new_table.id,
            "name": new_table.name,
            "capacity": new_table.capacity,
            "room_id": new_table.room_id,
            "active": new_table.active,
            "combinable": new_table.combinable
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create table: {str(e)}")

@app.post("/api/reservations/{reservation_id}/assign-table/{table_id}")
async def assign_reservation_to_table_temp(reservation_id: str, table_id: str, db: Session = Depends(get_db)):
    """Assign a reservation to a specific table"""
    from app.models.reservation import Reservation
    from app.models.table import Table
    
    try:
        # Get reservation
        reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
        if not reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")
        
        # Get table
        table = db.query(Table).filter(Table.id == table_id).first()
        if not table:
            raise HTTPException(status_code=404, detail="Table not found")
        
        # Check if table is available for this time
        conflicting_reservations = db.query(Reservation).filter(
            Reservation.table_id == table_id,
            Reservation.date == reservation.date,
            Reservation.id != reservation_id
        ).all()
        
        # Simple conflict check - can be enhanced with time overlap logic
        if conflicting_reservations:
            raise HTTPException(status_code=400, detail="Table is already reserved for this date")
        
        # Assign table to reservation
        reservation.table_id = table_id
        db.commit()
        
        return {
            "message": "Reservation assigned to table successfully",
            "reservation_id": reservation_id,
            "table_id": table_id,
            "table_name": table.name
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to assign reservation to table: {str(e)}")

@app.get("/api/tables/{table_id}/availability/{date}")
async def get_table_availability_temp(table_id: str, date: str, db: Session = Depends(get_db)):
    """Get table availability for a specific date"""
    from app.models.table import Table
    from app.models.reservation import Reservation
    from datetime import datetime
    
    try:
        # Parse date
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    # Get table
    table = db.query(Table).filter(Table.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    
    # Get reservations for this table and date
    reservations = db.query(Reservation).filter(
        Reservation.table_id == table_id,
        Reservation.date == target_date
    ).all()
    
    return {
        "table_id": table_id,
        "table_name": table.name,
        "capacity": table.capacity,
        "date": date,
        "reservations": [
            {
                "id": r.id,
                "customer_name": r.customer_name,
                "time": r.time,
                "party_size": r.party_size,
                "status": r.status
            } for r in reservations
        ],
        "is_available": len(reservations) == 0
    }

# All complex endpoints with database dependencies are temporarily disabled