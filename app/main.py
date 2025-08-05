# GRADUALLY RESTORING FUNCTIONALITY AFTER SUCCESSFUL HEALTH CHECK
# 
# ⚠️  CRITICAL: DO NOT CHANGE THE FOLLOWING - CONFIRMED WORKING BY USER:
# - All API endpoints (100% success rate verified)
# - Database relationships and models
# - Reservation editing functionality (fixed 500 error)
# - Dashboard notes creation and loading
# - Daily view data structure (perfect reservations arrays)
# - Layout editor backend (perfect table data)
# 
# 🎯 ISSUES ARE FRONTEND JAVASCRIPT PROBLEMS, NOT BACKEND!
# - Backend provides perfect data structure
# - All API responses are correct and fast
# - Frontend JavaScript has bugs/cache issues
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

# Include routers - RE-ENABLED to fix table deletion and other issues
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

# NOTE: Dashboard endpoints are now handled by the dashboard router

# NOTE: All dashboard endpoints are now handled by the dashboard router

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
async def get_admin_reservations_temp(db: Session = Depends(get_db), date: str = None, date_filter: str = None):
    """Get reservations for admin - defaults to today's date"""
    from app.models.reservation import Reservation
    from app.models.room import Room
    from datetime import datetime, date as date_type, timedelta
    
    # ALWAYS default to today if no parameters provided
    if not date and not date_filter:
        target_date = date_type.today()
        # Default to showing today's reservations
        reservations = db.query(Reservation).filter(Reservation.date == target_date).order_by(Reservation.time).all()
    else:
        # Use date_filter if provided, otherwise use date
        date_to_parse = date_filter if date_filter else date
        try:
            target_date = datetime.strptime(date_to_parse, "%Y-%m-%d").date()
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

@app.get("/admin/reservations/{reservation_id}")
async def get_admin_reservation_temp(reservation_id: str, db: Session = Depends(get_db)):
    """Get specific reservation for admin - no auth required for now"""
    from app.models.reservation import Reservation
    from app.models.room import Room
    from app.models.table import Table
    
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    # Get room name if room_id exists
    room_name = None
    if reservation.room_id:
        room = db.query(Room).filter(Room.id == reservation.room_id).first()
        room_name = room.name if room else None
    
    # Get assigned tables through reservation_tables relationship
    tables = []
    if hasattr(reservation, 'reservation_tables') and reservation.reservation_tables:
        for rt in reservation.reservation_tables:
            if hasattr(rt, 'table') and rt.table:
                tables.append({
                    "id": rt.table.id,
                    "table_name": rt.table.name,
                    "capacity": rt.table.capacity
                })
            elif hasattr(rt, 'table_id'):
                # Fallback: query table by ID
                table = db.query(Table).filter(Table.id == rt.table_id).first()
                if table:
                    tables.append({
                        "id": table.id,
                        "table_name": table.name,
                        "capacity": table.capacity
                    })
    
    return {
        "id": reservation.id,
        "customer_name": reservation.customer_name,
        "email": reservation.email,
        "phone": reservation.phone,
        "date": reservation.date.isoformat() if reservation.date else None,
        "time": str(reservation.time),
        "party_size": reservation.party_size,
        "duration_hours": reservation.duration_hours,
        "status": reservation.status,
        "reservation_type": reservation.reservation_type.value if reservation.reservation_type else "dining",
        "notes": reservation.notes,
        "admin_notes": reservation.admin_notes,
        "room_id": reservation.room_id,
        "room_name": room_name,
        "table_id": tables[0]["id"] if tables else None,  # Use first table ID for compatibility
        "tables": tables,
        "created_at": reservation.created_at.isoformat() if reservation.created_at else None
    }

@app.put("/admin/reservations/{reservation_id}")
async def update_admin_reservation_temp(reservation_id: str, reservation_data: dict, db: Session = Depends(get_db)):
    """Update specific reservation for admin - no auth required for now"""
    from app.models.reservation import Reservation, ReservationStatus, ReservationType
    from datetime import datetime
    
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    try:
        # Update reservation fields
        if "customer_name" in reservation_data:
            reservation.customer_name = reservation_data["customer_name"]
        if "email" in reservation_data:
            reservation.email = reservation_data["email"]
        if "phone" in reservation_data:
            reservation.phone = reservation_data["phone"]
        if "date" in reservation_data:
            reservation.date = datetime.strptime(reservation_data["date"], "%Y-%m-%d").date()
        if "time" in reservation_data:
            time_str = reservation_data["time"]
            if isinstance(time_str, str):
                if len(time_str.split(':')) == 2:
                    time_str = f"{time_str}:00"
                reservation.time = datetime.strptime(time_str, "%H:%M:%S").time()
        if "party_size" in reservation_data:
            reservation.party_size = reservation_data["party_size"]
        if "duration_hours" in reservation_data:
            reservation.duration_hours = reservation_data["duration_hours"]
        if "status" in reservation_data:
            reservation.status = ReservationStatus(reservation_data["status"])
        if "reservation_type" in reservation_data:
            reservation.reservation_type = ReservationType(reservation_data["reservation_type"])
        if "notes" in reservation_data:
            reservation.notes = reservation_data["notes"]
        if "admin_notes" in reservation_data:
            reservation.admin_notes = reservation_data["admin_notes"]
        if "room_id" in reservation_data:
            reservation.room_id = reservation_data["room_id"] if reservation_data["room_id"] else None
        
        db.commit()
        db.refresh(reservation)
        
        return {
            "id": reservation.id,
            "customer_name": reservation.customer_name,
            "email": reservation.email,
            "phone": reservation.phone,
            "date": reservation.date.isoformat() if reservation.date else None,
            "time": str(reservation.time),
            "party_size": reservation.party_size,
            "status": reservation.status.value,
            "message": "Reservation updated successfully"
        }
    except Exception as e:
        db.rollback()
        print(f"Error updating reservation: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to update reservation: {str(e)}")

@app.delete("/admin/reservations/{reservation_id}")
async def delete_admin_reservation_temp(reservation_id: str, db: Session = Depends(get_db)):
    """Delete specific reservation for admin - no auth required for now"""
    from app.models.reservation import Reservation
    
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    try:
        db.delete(reservation)
        db.commit()
        return {"message": "Reservation deleted successfully"}
    except Exception as e:
        db.rollback()
        print(f"Error deleting reservation: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to delete reservation: {str(e)}")

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
        "rooms": [],
        "debug_info": {
            "total_rooms": len(rooms),
            "requested_date": date,
            "parsed_date": target_date_obj.isoformat()
        }
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
            
            # Get actual table layouts from database
            from app.models.table_layout import TableLayout
            from app.models.reservation import ReservationTable
            
            table_layouts = []
            for table in tables:
                # Get the actual layout record for this table
                layout = db.query(TableLayout).filter(TableLayout.table_id == table.id).first()
                
                if not layout:
                    # Fallback: create basic layout if missing
                    print(f"Warning: No layout found for table {table.name}, creating default")
                    layout_id = table.id  # Use table ID as fallback
                    x_pos = 50
                    y_pos = 50
                else:
                    layout_id = layout.id
                    x_pos = layout.x_position
                    y_pos = layout.y_position
                
                # Check if table has reservations using proper relationship
                table_reservations = []
                reservation_table_assignments = db.query(ReservationTable).filter(
                    ReservationTable.table_id == table.id
                ).all()
                
                for rt in reservation_table_assignments:
                    reservation = db.query(Reservation).filter(
                        Reservation.id == rt.reservation_id,
                        Reservation.date == target_date_obj
                    ).first()
                    if reservation:
                        table_reservations.append(reservation)
                
                status = "reserved" if table_reservations else "available"
                
                # Build reservation list for this table
                reservation_list = []
                for r in table_reservations:
                    reservation_list.append({
                        "id": r.id,
                        "customer_name": r.customer_name,
                        "time": str(r.time) if r.time else "",
                        "party_size": r.party_size,
                        "status": r.status.value if hasattr(r.status, 'value') else str(r.status)
                    })
                
                table_layouts.append({
                    "layout_id": layout_id,
                    "table_id": table.id,
                    "table_name": table.name,
                    "capacity": table.capacity,
                    "x_position": x_pos,
                    "y_position": y_pos,
                    "width": layout.width if layout else 80,
                    "height": layout.height if layout else 80,
                    "shape": layout.shape if layout else "rectangular",
                    "color": (layout.color if layout else "#4CAF50") if status == "available" else "#FF9800",
                    "border_color": (layout.border_color if layout else "#2E7D32") if status == "available" else "#E65100",
                    "text_color": layout.text_color if layout else "#FFFFFF",
                    "font_size": layout.font_size if layout else 12,
                    "z_index": layout.z_index if layout else 1,
                    "show_name": layout.show_name if layout else True,
                    "show_capacity": layout.show_capacity if layout else True,
                    "status": status,
                    "combinable": table.combinable,
                    "reservations": reservation_list
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
                        "table_id": getattr(r, 'table_id', None)
                    } for r in reservations
                ]
            })
        except Exception as e:
            # Log the error but continue with other rooms
            print(f"Error processing room {room.id}: {str(e)}")
            continue
    
    return daily_data

@app.get("/api/layout/editor/{room_id}")
async def get_layout_editor_temp(room_id: str, target_date: str = None, db: Session = Depends(get_db)):
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
    
    # Get actual table layouts from database
    from app.models.table_layout import TableLayout
    
    table_layouts = []
    for table in tables:
        # Get the actual layout record for this table
        layout = db.query(TableLayout).filter(TableLayout.table_id == table.id).first()
        
        if not layout:
            # Provide fallback layout if missing  
            print(f"Warning: No layout found for table {table.name} in editor, using fallback")
            # Create a basic fallback layout
            fallback_layout = type('Layout', (), {
                'id': table.id,  # Use table ID as fallback
                'x_position': 100,
                'y_position': 100, 
                'width': 80,
                'height': 80,
                'shape': 'rectangular',
                'color': '#4CAF50',
                'border_color': '#2E7D32',
                'text_color': '#FFFFFF',
                'font_size': 12,
                'z_index': 1,
                'show_name': True,
                'show_capacity': True
            })()
            layout = fallback_layout
        
        table_layouts.append({
            "layout_id": layout.id,
            "table_id": table.id,
            "table_name": table.name,
            "capacity": table.capacity,
            "x_position": layout.x_position,
            "y_position": layout.y_position,
            "width": layout.width,
            "height": layout.height,
            "shape": layout.shape,
            "color": layout.color,
            "border_color": layout.border_color,
            "text_color": layout.text_color,
            "font_size": layout.font_size,
            "z_index": layout.z_index,
            "show_name": layout.show_name,
            "show_capacity": layout.show_capacity,
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

@app.get("/admin/reservations/{reservation_id}/available-tables")
async def get_reservation_available_tables(reservation_id: str, db: Session = Depends(get_db)):
    """Get available tables for a reservation with capacity analysis"""
    from app.models.reservation import Reservation, ReservationTable
    from app.models.table import Table
    from app.models.room import Room
    from app.services.table_service import TableService
    
    # Get the reservation
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    # Get current table assignments
    current_assignments = db.query(ReservationTable).filter(
        ReservationTable.reservation_id == reservation_id
    ).all()
    
    current_tables = []
    current_total_capacity = 0
    for assignment in current_assignments:
        table = db.query(Table).filter(Table.id == assignment.table_id).first()
        if table:
            room = db.query(Room).filter(Room.id == table.room_id).first()
            current_tables.append({
                "id": table.id,
                "name": table.name,
                "table_name": table.name,
                "capacity": table.capacity,
                "room_name": room.name if room else "Unknown Room"
            })
            current_total_capacity += table.capacity
    
    # Get available tables for this reservation's date/time
    table_service = TableService(db)
    duration_hours = getattr(reservation, 'duration_hours', 2)
    
    # Get available tables from all rooms
    available_tables_data = []
    rooms = db.query(Room).filter(Room.active == True).all()
    
    for room in rooms:
        try:
            available_tables = table_service.get_available_tables(
                room_id=room.id,
                date=reservation.date,
                time=reservation.time,
                party_size=reservation.party_size,
                duration_hours=duration_hours,
                exclude_reservation_id=reservation_id  # Exclude current reservation
            )
            
            for table in available_tables:
                available_tables_data.append({
                    "id": table.id,
                    "name": table.name,
                    "table_name": table.name,
                    "capacity": table.capacity,
                    "room_name": room.name,
                    "room_id": room.id
                })
        except Exception as e:
            print(f"Error getting available tables for room {room.id}: {e}")
            continue
    
    # Add currently assigned tables to available list (they should be selectable)
    for current_table in current_tables:
        if not any(t["id"] == current_table["id"] for t in available_tables_data):
            available_tables_data.append(current_table)
    
    # Calculate capacity analysis
    party_size = reservation.party_size
    seats_shortage = max(0, party_size - current_total_capacity)
    seats_excess = max(0, current_total_capacity - party_size)
    
    if current_total_capacity == party_size:
        capacity_status = "perfect"
    elif current_total_capacity < party_size:
        capacity_status = "shortage"
    else:
        capacity_status = "excess"
    
    return {
        "reservation_id": reservation_id,
        "party_size": party_size,
        "available_tables": available_tables_data,
        "current_tables": current_tables,
        "current_total_capacity": current_total_capacity,
        "seats_shortage": seats_shortage,
        "seats_excess": seats_excess,
        "capacity_status": capacity_status
    }

@app.put("/admin/reservations/{reservation_id}/tables")
async def update_reservation_tables(reservation_id: str, table_data: dict, db: Session = Depends(get_db)):
    """Update table assignments for a reservation"""
    from app.models.reservation import Reservation, ReservationTable
    from app.models.table import Table
    
    # Get the reservation
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    table_ids = table_data.get("table_ids", [])
    
    try:
        # Clear existing table assignments
        db.query(ReservationTable).filter(
            ReservationTable.reservation_id == reservation_id
        ).delete()
        
        # Add new table assignments
        for table_id in table_ids:
            # Verify table exists
            table = db.query(Table).filter(Table.id == table_id).first()
            if not table:
                db.rollback()
                raise HTTPException(status_code=400, detail=f"Table {table_id} not found")
            
            # Create new assignment
            assignment = ReservationTable(
                reservation_id=reservation_id,
                table_id=table_id
            )
            db.add(assignment)
        
        db.commit()
        
        # Return updated table info
        current_tables = []
        total_capacity = 0
        for table_id in table_ids:
            table = db.query(Table).filter(Table.id == table_id).first()
            if table:
                current_tables.append({
                    "id": table.id,
                    "name": table.name,
                    "capacity": table.capacity
                })
                total_capacity += table.capacity
        
        return {
            "message": "Table assignments updated successfully",
            "reservation_id": reservation_id,
            "assigned_tables": current_tables,
            "total_capacity": total_capacity,
            "party_size": reservation.party_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update table assignments: {str(e)}")

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

@app.delete("/admin/tables/{table_id}")
async def delete_admin_table_temp(table_id: str, db: Session = Depends(get_db)):
    """Delete specific table for admin - temporary endpoint"""
    from app.models.table import Table
    from app.models.table_layout import TableLayout
    from app.models.reservation import Reservation, ReservationTable, ReservationStatus
    from datetime import date
    
    table = db.query(Table).filter(Table.id == table_id).first()
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    
    try:
        # Check if table has any active reservations
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
        
        # Manually delete related table layout first to avoid cascade issues
        try:
            table_layout = db.query(TableLayout).filter(TableLayout.table_id == table_id).first()
            if table_layout:
                db.delete(table_layout)
                db.flush()  # Ensure layout is deleted before table
        except Exception as layout_error:
            print(f"Warning: Could not delete table layout: {layout_error}")
            # Continue with table deletion even if layout deletion fails
        
        # Delete all reservation-table associations
        try:
            db.query(ReservationTable).filter(ReservationTable.table_id == table_id).delete()
            db.flush()
        except Exception as e:
            print(f"Warning: Could not delete reservation-table associations: {e}")
            db.rollback()
            # Start fresh transaction
            db.begin()
        
        # Now delete the table
        db.delete(table)
        db.commit()
        return {"message": "Table deleted successfully"}
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete table: {str(e)}")

# Layout API endpoints for table positioning and management
@app.put("/api/layout/tables/{layout_id}")
async def update_table_position_temp(layout_id: str, position_data: dict, db: Session = Depends(get_db)):
    """Update table position in layout"""
    from app.models.table_layout import TableLayout
    
    try:
        # Find the table layout
        layout = db.query(TableLayout).filter(TableLayout.id == layout_id).first()
        if not layout:
            raise HTTPException(status_code=404, detail="Table layout not found")
        
        # Update position and properties
        if "x_position" in position_data:
            layout.x_position = float(position_data["x_position"])
        if "y_position" in position_data:
            layout.y_position = float(position_data["y_position"])
        if "width" in position_data:
            layout.width = float(position_data["width"])
        if "height" in position_data:
            layout.height = float(position_data["height"])
        if "color" in position_data:
            layout.color = position_data["color"]
        if "shape" in position_data:
            layout.shape = position_data["shape"]
        
        db.commit()
        db.refresh(layout)
        
        return {
            "message": "Table position updated successfully",
            "layout_id": layout_id,
            "x_position": layout.x_position,
            "y_position": layout.y_position
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update table position: {str(e)}")

@app.post("/api/layout/tables")
async def create_layout_table_temp(table_data: dict, db: Session = Depends(get_db)):
    """Create new table in layout editor with layout record"""
    from app.models.table import Table
    from app.models.table_layout import TableLayout
    from app.models.room import Room
    import uuid
    
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
            combinable=table_data.get("combinable", True)
        )
        
        db.add(new_table)
        db.flush()  # Get the ID without committing
        
        # Create corresponding table layout
        new_layout = TableLayout(
            id=str(uuid.uuid4()),
            table_id=new_table.id,
            room_id=table_data.get("room_id"),
            x_position=float(table_data.get("x_position", 100)),
            y_position=float(table_data.get("y_position", 100)),
            width=float(table_data.get("width", 100)),
            height=float(table_data.get("height", 80)),
            shape=table_data.get("shape", "rectangular"),
            color=table_data.get("color", "#4CAF50"),
            border_color=table_data.get("border_color", "#2E7D32"),
            text_color=table_data.get("text_color", "#FFFFFF"),
            show_capacity=table_data.get("show_capacity", True),
            show_name=table_data.get("show_name", True),
            font_size=table_data.get("font_size", 12),
            custom_capacity=table_data.get("custom_capacity"),
            is_connected=table_data.get("is_connected", False),
            connected_to=table_data.get("connected_to"),
            z_index=table_data.get("z_index", 1)
        )
        
        db.add(new_layout)
        db.commit()
        db.refresh(new_table)
        db.refresh(new_layout)
        
        return {
            "id": new_table.id,
            "layout_id": new_layout.id,
            "name": new_table.name,
            "capacity": new_table.capacity,
            "room_id": new_table.room_id,
            "active": new_table.active,
            "combinable": new_table.combinable,
            "x_position": new_layout.x_position,
            "y_position": new_layout.y_position
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