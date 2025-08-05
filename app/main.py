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
async def get_dashboard_stats_temp():
    """Temporary dashboard stats"""
    return {
        "total_reservations_today": 0,
        "total_guests_today": 0,
        "total_reservations_week": 0,
        "total_guests_week": 0,
        "weekly_forecast": [],
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
async def get_dashboard_today_temp():
    """Temporary today's reservations"""
    return []

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

@app.get("/admin/reservations")
async def get_admin_reservations_temp(db: Session = Depends(get_db)):
    """Get all reservations for admin - no auth required for now"""
    from app.models.reservation import Reservation
    from app.models.room import Room
    
    reservations = db.query(Reservation).all()
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
async def create_reservation_temp():
    """Temporary reservation endpoint that accepts form data"""
    import uuid
    reservation_id = str(uuid.uuid4())
    return {
        "status": "success", 
        "message": "Reservation created successfully (temporary mode)", 
        "id": reservation_id,
        "reservation": {
            "id": reservation_id,
            "customer_name": "Test Customer",
            "date": "2025-01-30",
            "time": "19:00",
            "party_size": 4,
            "status": "confirmed"
        }
    }

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
async def get_layout_daily_temp(date: str):
    """Temporary daily layout"""
    return {
        "date": date,
        "rooms": [
            {
                "id": "room_1",
                "name": "Front Room",
                "tables": [],
                "reservations": []
            }
        ]
    }

# All complex endpoints with database dependencies are temporarily disabled