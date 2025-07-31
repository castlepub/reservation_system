# Import local configuration first to set environment variables
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
try:
    import local_config
    print("✓ Local configuration loaded")
except ImportError:
    print("⚠ Local configuration not found, using default settings")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.database import engine, Base
from app.api import auth, admin, public
# Import all models to ensure they're registered with SQLAlchemy
from app.models import User, Room, Table, Reservation, ReservationTable
from app.core.config import settings
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="The Castle Pub Reservation System",
    description="A comprehensive restaurant reservation system with table management and visual layout",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(admin.router, prefix="/admin")
app.include_router(public.router, prefix="/api")

# Import and include dashboard router
from app.api import dashboard
app.include_router(dashboard.router, prefix="/api")

# Import and include settings router
from app.api import settings as settings_router
app.include_router(settings_router.router, prefix="/api")

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    print(f"✓ Static files mounted from: {os.path.abspath(static_dir)}")
else:
    print(f"⚠ Static directory not found: {os.path.abspath(static_dir)}")

@app.get("/")
async def root():
    """Serve the main HTML file"""
    # Serve the HTML file instead of JSON
    html_file = os.path.join(static_dir, "index.html")
    if os.path.exists(html_file):
        return FileResponse(html_file)
    else:
        return {
            "message": "The Castle Pub Reservation System",
            "status": "running",
            "version": "1.0.0",
            "error": "HTML file not found"
        }

@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong"}

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "The Castle Pub Reservation System",
        "version": "1.0.0"
    }

@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {
        "message": "The Castle Pub Reservation System API",
        "status": "running",
        "endpoints": {
            "auth": "/api/auth",
            "admin": "/admin",
            "public": "/api/public",
            "dashboard": "/api/dashboard",
            "settings": "/api/settings"
        }
    }

@app.get("/api/dashboard/stats")
async def get_dashboard_stats_simple():
    """Simple dashboard stats endpoint for debugging"""
    return {
        "total_reservations_today": 0,
        "total_guests_today": 0,
        "total_reservations_week": 0,
        "total_guests_week": 0,
        "weekly_forecast": [],
        "guest_notes": []
    }

@app.get("/api/dashboard/customers")
async def get_customers_simple():
    """Simple customers endpoint for debugging"""
    return []

@app.get("/api/dashboard/notes")
async def get_dashboard_notes_simple():
    """Simple dashboard notes endpoint for debugging"""
    return []

@app.get("/api/dashboard/today")
async def get_today_reservations_simple():
    """Simple today's reservations endpoint for debugging"""
    return []



@app.get("/api/test-auth")
async def test_auth():
    """Test auth endpoint"""
    return {"message": "Auth router is working", "status": "ok"}

@app.get("/api/layout/editor/{room_id}")
async def get_layout_editor_fallback(room_id: str, target_date: str = None):
    """Fallback endpoint for layout editor while layout system is being fixed"""
    return {
        "room_id": room_id,
        "room_layout": {
            "id": f"temp_{room_id}",
            "room_id": room_id,
            "width": 800.0,
            "height": 600.0,
            "background_color": "#F5F5F5",
            "grid_enabled": True,
            "grid_size": 20,
            "grid_color": "#E0E0E0",
            "show_entrance": True,
            "entrance_position": "top",
            "show_bar": False,
            "bar_position": "center",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": None
        },
        "tables": [],
        "reservations": []
    }

@app.get("/api/layout/daily/{date}")
async def get_daily_view_fallback(date: str):
    """Fallback endpoint for daily layout view"""
    return {
        "date": date,
        "rooms": []
    }

@app.get("/admin/init-basic-data")
async def init_basic_data():
    """Initialize basic data (rooms and tables)"""
    try:
        from app.core.database import SessionLocal
        from app.models.room import Room
        from app.models.table import Table
        import uuid
        
        db = SessionLocal()
        try:
            # Check if rooms already exist
            existing_rooms = db.query(Room).count()
            if existing_rooms == 0:
                # Create basic rooms
                rooms = [
                    Room(
                        id=str(uuid.uuid4()),
                        name="Front Room",
                        active=True
                    ),
                    Room(
                        id=str(uuid.uuid4()),
                        name="Middle Room", 
                        active=True
                    ),
                    Room(
                        id=str(uuid.uuid4()),
                        name="Back Room",
                        active=True
                    ),
                    Room(
                        id=str(uuid.uuid4()),
                        name="Biergarten",
                        active=True
                    )
                ]
                
                for room in rooms:
                    db.add(room)
                
                db.commit()
                
                # Create basic tables for each room
                for room in rooms:
                    for i in range(1, 6):  # 5 tables per room
                        table = Table(
                            id=str(uuid.uuid4()),
                            name=f"{room.name[0]}{i}",  # F1, M1, B1, BG1, etc.
                            room_id=room.id,
                            capacity=4 + (i % 3) * 2,  # 4, 6, or 8 seats
                            active=True,
                            combinable=True
                        )
                        db.add(table)
                
                db.commit()
                return {"status": "success", "message": "Basic data initialized", "rooms_created": 4, "tables_created": 20}
            else:
                return {"status": "success", "message": "Data already exists", "existing_rooms": existing_rooms}
                
        finally:
            db.close()
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/admin/debug/check-data")
async def check_database_data():
    """Check what data exists in the database"""
    try:
        from app.core.database import SessionLocal
        from app.models.room import Room
        from app.models.table import Table
        from app.models.user import User
        
        db = SessionLocal()
        try:
            rooms_count = db.query(Room).count()
            tables_count = db.query(Table).count()
            users_count = db.query(User).count()
            
            rooms = []
            if rooms_count > 0:
                rooms = [
                    {
                        "id": str(room.id),
                        "name": room.name,
                        "active": room.active
                    }
                    for room in db.query(Room).all()
                ]
            
            tables = []
            if tables_count > 0:
                tables = [
                    {
                        "id": str(table.id),
                        "name": table.name,
                        "room_id": str(table.room_id),
                        "active": table.active
                    }
                    for table in db.query(Table).all()
                ]
            
            return {
                "rooms_count": rooms_count,
                "tables_count": tables_count,
                "users_count": users_count,
                "rooms": rooms,
                "tables": tables
            }
            
        finally:
            db.close()
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/admin/tables")
async def get_tables_simple():
    """Simple endpoint to get all tables"""
    try:
        from app.core.database import SessionLocal
        from app.models.table import Table
        from app.models.room import Room
        
        db = SessionLocal()
        try:
            tables = db.query(Table).all()
            rooms = db.query(Room).all()
            
            # Create room lookup
            room_lookup = {str(room.id): room.name for room in rooms}
            
            table_data = []
            for table in tables:
                table_data.append({
                    "id": str(table.id),
                    "name": table.name,
                    "room_id": str(table.room_id),
                    "room_name": room_lookup.get(str(table.room_id), "Unknown"),
                    "capacity": getattr(table, 'capacity', 4),
                    "combinable": getattr(table, 'combinable', True),
                    "active": table.active,
                    "description": getattr(table, 'description', '')
                })
            
            return table_data
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error getting tables: {e}")
        return []

@app.get("/admin/rooms")
async def get_rooms_simple():
    """Simple endpoint to get all rooms"""
    try:
        from app.core.database import SessionLocal
        from app.models.room import Room
        
        db = SessionLocal()
        try:
            rooms = db.query(Room).all()
            
            room_data = []
            for room in rooms:
                room_data.append({
                    "id": str(room.id),
                    "name": room.name,
                    "active": room.active,
                    "description": getattr(room, 'description', '')
                })
            
            return room_data
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error getting rooms: {e}")
        return []

@app.get("/admin/reservations")
async def get_reservations_simple(date_filter: str = None):
    """Simple endpoint to get reservations"""
    try:
        from app.core.database import SessionLocal
        from app.models.reservation import Reservation
        from app.models.room import Room
        
        db = SessionLocal()
        try:
            query = db.query(Reservation)
            
            if date_filter:
                from datetime import datetime
                try:
                    filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
                    query = query.filter(Reservation.date == filter_date)
                except ValueError:
                    pass
            
            reservations = query.all()
            rooms = db.query(Room).all()
            room_lookup = {str(room.id): room.name for room in rooms}
            
            reservation_data = []
            for reservation in reservations:
                reservation_data.append({
                    "id": str(reservation.id),
                    "customer_name": reservation.customer_name,
                    "date": reservation.date.strftime("%Y-%m-%d") if reservation.date else None,
                    "time": reservation.time.strftime("%H:%M") if reservation.time else None,
                    "party_size": reservation.party_size,
                    "reservation_type": reservation.reservation_type.value if reservation.reservation_type else "dining",
                    "status": reservation.status.value if reservation.status else "confirmed",
                    "room_name": room_lookup.get(str(reservation.room_id), "Unknown"),
                    "notes": reservation.notes,
                    "admin_notes": reservation.admin_notes,
                    "duration_hours": getattr(reservation, 'duration_hours', 2)
                })
            
            return reservation_data
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error getting reservations: {e}")
        return []

@app.get("/api/settings/restaurant")
async def get_restaurant_settings():
    """Get restaurant settings"""
    return {
        "name": "The Castle Pub",
        "phone": "+49 30 12345600",
        "address": "Kastanienallee 85, 10435 Berlin, Germany",
        "max_party_size": 20,
        "min_advance_hours": 2,
        "max_advance_days": 90
    }

@app.get("/api/settings/working-hours")
async def get_working_hours():
    """Get working hours"""
    return {
        "monday": {"open": True, "start": "11:00", "end": "23:00"},
        "tuesday": {"open": True, "start": "11:00", "end": "23:00"},
        "wednesday": {"open": True, "start": "11:00", "end": "23:00"},
        "thursday": {"open": True, "start": "11:00", "end": "23:00"},
        "friday": {"open": True, "start": "11:00", "end": "00:00"},
        "saturday": {"open": True, "start": "11:00", "end": "00:00"},
        "sunday": {"open": True, "start": "12:00", "end": "22:00"}
    }

@app.get("/api/rooms")
async def get_public_rooms():
    """Get public rooms for reservation form"""
    try:
        from app.core.database import SessionLocal
        from app.models.room import Room
        
        db = SessionLocal()
        try:
            rooms = db.query(Room).filter(Room.active == True).all()
            
            room_data = []
            for room in rooms:
                room_data.append({
                    "id": str(room.id),
                    "name": room.name,
                    "description": getattr(room, 'description', '')
                })
            
            return room_data
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error getting public rooms: {e}")
        return []

@app.get("/admin/reports/daily")
async def get_daily_report_simple(report_date: str):
    """Simple daily report endpoint"""
    try:
        from app.core.database import SessionLocal
        from app.models.reservation import Reservation
        from app.models.room import Room
        from datetime import datetime
        
        db = SessionLocal()
        try:
            # Parse date
            target_date = datetime.strptime(report_date, "%Y-%m-%d").date()
            
            # Get reservations for the date
            reservations = db.query(Reservation).filter(Reservation.date == target_date).all()
            rooms = db.query(Room).all()
            
            room_lookup = {str(room.id): room.name for room in rooms}
            
            reservation_data = []
            for reservation in reservations:
                reservation_data.append({
                    "id": str(reservation.id),
                    "customer_name": reservation.customer_name,
                    "time": reservation.time.strftime("%H:%M") if reservation.time else "00:00",
                    "party_size": reservation.party_size,
                    "reservation_type": reservation.reservation_type.value if reservation.reservation_type else "dining",
                    "status": reservation.status.value if reservation.status else "confirmed",
                    "room_name": room_lookup.get(str(reservation.room_id), "Unknown"),
                    "notes": reservation.notes,
                    "admin_notes": reservation.admin_notes,
                    "duration_hours": getattr(reservation, 'duration_hours', 2)
                })
            
            return {
                "date": report_date,
                "reservations": reservation_data,
                "total_reservations": len(reservation_data),
                "total_guests": sum(r["party_size"] for r in reservation_data)
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        return {
            "date": report_date,
            "reservations": [],
            "total_reservations": 0,
            "total_guests": 0,
            "error": str(e)
        }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.get("/init-db")
async def initialize_database():
    """Manually trigger database initialization"""
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        return {"status": "success", "message": "Database initialized"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/create-admin")
async def create_admin_user():
    """Create a default admin user for testing"""
    try:
        from app.core.database import SessionLocal
        from app.models.user import User, UserRole
        from app.core.security import get_password_hash
        import uuid
        
        db = SessionLocal()
        try:
            # Check if admin user already exists
            existing_admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
            if existing_admin:
                return {"status": "success", "message": "Admin user already exists", "username": existing_admin.username}
            
            # Create admin user
            admin_user = User(
                id=str(uuid.uuid4()),
                username="admin",
                password_hash=get_password_hash("admin123"),
                role=UserRole.ADMIN
            )
            
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            return {
                "status": "success", 
                "message": "Admin user created", 
                "username": "admin",
                "password": "admin123"
            }
            
        finally:
            db.close()
            
    except Exception as e:
        return {"status": "error", "message": str(e)} 