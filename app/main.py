# GRADUALLY RESTORING FUNCTIONALITY AFTER SUCCESSFUL HEALTH CHECK
import os
from datetime import datetime
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
async def get_rooms_settings_temp():
    """Temporary rooms settings - no auth required"""
    return [
        {
            "id": "room_1",
            "name": "Front Room",
            "description": "Front dining area with window views",
            "active": True,
            "created_at": "2025-01-30T10:00:00",
            "updated_at": "2025-01-30T10:00:00"
        },
        {
            "id": "room_2", 
            "name": "Back Room",
            "description": "Back dining area for larger groups",
            "active": True,
            "created_at": "2025-01-30T10:00:00",
            "updated_at": "2025-01-30T10:00:00"
        },
        {
            "id": "room_3",
            "name": "Middle Room",
            "description": "Middle dining area with flexible seating",
            "active": True,
            "created_at": "2025-01-30T10:00:00",
            "updated_at": "2025-01-30T10:00:00"
        },
        {
            "id": "room_4",
            "name": "Biergarten",
            "description": "Outdoor beer garden seating",
            "active": True,
            "created_at": "2025-01-30T10:00:00",
            "updated_at": "2025-01-30T10:00:00"
        }
    ]

@app.post("/api/settings/rooms")
async def create_room_settings_temp():
    """Temporary create room - no auth required"""
    return {
        "id": "new_room_1",
        "name": "New Room",
        "description": "New room created",
        "active": True,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

@app.put("/api/settings/rooms/{room_id}")
async def update_room_settings_temp(room_id: str):
    """Temporary update room - no auth required"""
    return {
        "id": room_id,
        "name": "Updated Room",
        "description": "Room updated",
        "active": True,
        "created_at": "2025-01-30T10:00:00",
        "updated_at": datetime.utcnow().isoformat()
    }

@app.delete("/api/settings/rooms/{room_id}")
async def delete_room_settings_temp(room_id: str):
    """Temporary delete room - no auth required"""
    return {"message": "Room deleted successfully"}

@app.get("/api/settings/special-days")
async def get_special_days_temp():
    """Temporary special days - no auth required"""
    return []

# Admin endpoints are handled by the admin router

# Admin endpoints are now handled by the admin router

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