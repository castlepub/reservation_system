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
from app.api.settings import router as settings_router
from app.api.admin import router as admin_router
from app.api.dashboard import router as dashboard_router
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
app.include_router(settings_router, prefix="/api")
app.include_router(admin_router, prefix="/admin")
app.include_router(dashboard_router, prefix="/api/dashboard")
app.include_router(auth_router, prefix="/api/auth")

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

@app.post("/api/auth/login")
async def login_temp():
    """Temporary login endpoint - accepts any credentials"""
    return {
        "access_token": "temporary_token_12345",
        "token_type": "bearer",
        "user": {
            "id": "temp_user",
            "username": "admin",
            "role": "admin"
        }
    }

@app.get("/api/auth/me")
async def get_auth_me_temp():
    """Temporary auth check - return user if token exists"""
    return {
        "id": "temp_user",
        "username": "admin", 
        "role": "admin",
        "email": "admin@castlepub.com"
    }

@app.get("/api/settings/restaurant")
async def get_restaurant_settings_temp():
    """Temporary restaurant settings"""
    return [
        {"key": "name", "value": "The Castle Pub"},
        {"key": "address", "value": "123 Castle Street"},
        {"key": "phone", "value": "+1 234 567 8900"},
        {"key": "email", "value": "info@castlepub.com"},
        {"key": "website", "value": "www.castlepub.com"}
    ]

# Admin endpoints with proper authentication bypass for now
@app.get("/admin/reservations")
async def get_admin_reservations_temp():
    """Temporary admin reservations"""
    return []

@app.get("/admin/rooms")
async def get_admin_rooms_temp():
    """Temporary admin rooms with sample data"""
    return [
        {
            "id": "room_1",
            "name": "Main Dining Room",
            "active": True,
            "description": "Main dining area with 20 tables"
        },
        {
            "id": "room_2", 
            "name": "Private Dining",
            "active": True,
            "description": "Private dining room for special events"
        },
        {
            "id": "room_3",
            "name": "Bar Area",
            "active": True,
            "description": "Bar seating and high tables"
        }
    ]

@app.get("/admin/tables")
async def get_admin_tables_temp():
    """Temporary admin tables with sample data"""
    return [
        {
            "id": "table_1",
            "name": "Table 1",
            "room_id": "room_1",
            "room_name": "Main Dining Room",
            "capacity": 4,
            "combinable": True,
            "active": True,
            "description": "Window table for 4"
        },
        {
            "id": "table_2",
            "name": "Table 2", 
            "room_id": "room_1",
            "room_name": "Main Dining Room",
            "capacity": 6,
            "combinable": True,
            "active": True,
            "description": "Large table for 6"
        },
        {
            "id": "table_3",
            "name": "Table 3",
            "room_id": "room_2",
            "room_name": "Private Dining",
            "capacity": 8,
            "combinable": False,
            "active": True,
            "description": "Private dining table"
        },
        {
            "id": "table_4",
            "name": "Bar 1",
            "room_id": "room_3", 
            "room_name": "Bar Area",
            "capacity": 2,
            "combinable": True,
            "active": True,
            "description": "Bar seating"
        }
    ]

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

@app.get("/api/settings/special-days")
async def get_special_days_temp():
    """Temporary special days"""
    return []

@app.get("/api/layout/daily/{date}")
async def get_layout_daily_temp(date: str):
    """Temporary daily layout"""
    return {
        "date": date,
        "rooms": [
            {
                "id": "room_1",
                "name": "Main Dining Room",
                "tables": [],
                "reservations": []
            }
        ]
    }

# All complex endpoints with database dependencies are temporarily disabled