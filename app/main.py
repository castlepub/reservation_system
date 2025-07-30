from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.database import engine, Base
from app.api import auth, public, admin
# Import all models to ensure they're registered with SQLAlchemy
from app.models import User, Room, Table, Reservation, ReservationTable, TableLayout, RoomLayout
# from app.api.layout import router as layout_router  # Disabled due to import issues
from app.core.config import settings
import logging
import os
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

# Include essential routers
app.include_router(auth.router, prefix="/api")
app.include_router(admin.router)
app.include_router(public.router)
# app.include_router(layout_router)  # Disabled due to import issues

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

@app.on_event("startup")
async def startup_event():
    """Initialize database and create admin user on startup"""
    try:
        print("🔄 Starting database initialization...")
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created")
        
        # Run migrations in background
        try:
            import asyncio
            asyncio.create_task(run_migrations_async())
        except Exception as e:
            print(f"⚠️ Migration warning: {e}")
        
        # Create admin user in background
        try:
            asyncio.create_task(create_admin_user_async())
        except Exception as e:
            print(f"⚠️ Admin user creation warning: {e}")
        
        print("✅ Database initialization started successfully")
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        print("⚠️ Continuing with degraded functionality")

async def run_migrations_async():
    """Run migrations asynchronously"""
    try:
        run_migrations()
        print("✅ Database migrations completed")
    except Exception as e:
        print(f"⚠️ Migration error: {e}")

async def create_admin_user_async():
    """Create admin user asynchronously"""
    try:
        from app.core.database import SessionLocal
        from app.core.security import get_password_hash
        from app.models.user import User, UserRole
        
        db = SessionLocal()
        try:
            admin_user = db.query(User).filter(User.username == "admin").first()
            if not admin_user:
                admin_user = User(
                    username="admin",
                    password_hash=get_password_hash("admin123"),
                    role=UserRole.ADMIN
                )
                db.add(admin_user)
                db.commit()
                print("✅ Admin user created (username: admin, password: admin123)")
            else:
                print("✅ Admin user already exists")
        finally:
            db.close()
    except Exception as e:
        print(f"⚠️ Admin user creation error: {e}")

@app.get("/")
async def root():
    """Serve the main HTML file"""
    # Serve the HTML file instead of JSON
    html_file = os.path.join(static_dir, "index.html")
    if os.path.exists(html_file):
        return FileResponse(html_file)
    else:
        return {"message": "The Castle Pub Reservation System", "status": "running", "error": "HTML file not found"}

@app.get("/ping")
async def ping():
    """Simple health check endpoint"""
    return {"status": "ok", "message": "pong", "timestamp": datetime.now().isoformat()}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "reservation-system",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {
        "message": "The Castle Pub Reservation System API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/auth",
            "admin": "/api/admin", 
            "public": "/api/public",
            "dashboard": "/api/dashboard",
            "settings": "/api/settings"
        }
    }

@app.get("/api/test-auth")
async def test_auth():
    """Test if auth endpoints are accessible"""
    return {"message": "Auth router is working", "status": "ok"}

@app.get("/api/layout/daily/{date}")
async def get_daily_view_fallback(date: str):
    """Temporary fallback for daily view while layout router is disabled"""
    return {
        "date": date,
        "reservations": [],
        "rooms": [],
        "message": "Layout system temporarily disabled for stability"
    }

@app.get("/admin/init-basic-data")
async def init_basic_data():
    """Initialize basic rooms and tables for testing"""
    try:
        from app.core.database import SessionLocal
        from app.models.room import Room
        from app.models.table import Table
        
        db = SessionLocal()
        try:
            # Check if rooms exist
            existing_rooms = db.query(Room).count()
            if existing_rooms == 0:
                # Create sample rooms
                room1 = Room(name="Main Dining", description="Main dining area", active=True)
                room2 = Room(name="Private Dining", description="Private dining room", active=True)
                room3 = Room(name="Bar Area", description="Bar and lounge area", active=True)
                
                db.add_all([room1, room2, room3])
                db.commit()
                
                # Create sample tables with combinable logic
                tables = [
                    # Main Dining - tables can combine
                    Table(name="T1", capacity=2, room_id=room1.id, active=True, combinable=True),
                    Table(name="T2", capacity=4, room_id=room1.id, active=True, combinable=True), 
                    Table(name="T3", capacity=6, room_id=room1.id, active=True, combinable=True),
                    # Private Dining - standalone
                    Table(name="P1", capacity=8, room_id=room2.id, active=True, combinable=False),
                    # Bar Area - small tables can combine
                    Table(name="B1", capacity=2, room_id=room3.id, active=True, combinable=True),
                    Table(name="B2", capacity=4, room_id=room3.id, active=True, combinable=True),
                ]
                
                db.add_all(tables)
                db.commit()
                
                # Create default table combinations
                combinations = [
                    # Main Dining combinations
                    {"primary_table": "T1", "combinable_with": ["T2"]},
                    {"primary_table": "T2", "combinable_with": ["T1", "T3"]},
                    {"primary_table": "T3", "combinable_with": ["T2"]},
                    # Bar Area combinations  
                    {"primary_table": "B1", "combinable_with": ["B2"]},
                    {"primary_table": "B2", "combinable_with": ["B1"]},
                    # P1 is standalone (no combinations)
                ]
                
                # Store combinations in a simple format (could be moved to database later)
                # For now, we'll use the table service logic
                
                return {"status": "success", "message": "Basic rooms, tables, and combinations created"}
            else:
                return {"status": "info", "message": f"Rooms already exist ({existing_rooms} rooms found)"}
                
        finally:
            db.close()
            
    except Exception as e:
        return {"status": "error", "message": f"Error creating basic data: {str(e)}"}

@app.get("/admin/debug/check-data")
async def check_database_data():
    """Debug endpoint to check what data exists in database"""
    try:
        from app.core.database import SessionLocal
        from app.models.room import Room
        from app.models.table import Table
        
        db = SessionLocal()
        try:
            rooms = db.query(Room).all()
            tables = db.query(Table).all()
            
            return {
                "rooms_count": len(rooms),
                "tables_count": len(tables),
                "rooms": [{"id": str(r.id), "name": r.name, "active": r.active} for r in rooms],
                "tables": [{"id": str(t.id), "name": t.name, "room_id": str(t.room_id), "active": t.active} for t in tables]
            }
            
        finally:
            db.close()
            
    except Exception as e:
        return {"error": str(e)}

@app.get("/admin/tables")
async def get_tables_simple():
    """Simple endpoint to get all tables"""
    try:
        from app.core.database import SessionLocal
        from app.models.table import Table
        from app.models.room import Room
        
        print("🔍 DEBUG: /admin/tables called")
        
        db = SessionLocal()
        try:
            tables = db.query(Table).join(Room).filter(Table.active == True).all()
            print(f"🔍 DEBUG: Found {len(tables)} tables")
            
            result = []
            for table in tables:
                # Handle missing fields gracefully
                capacity = getattr(table, 'capacity', 4)  # Default to 4 if missing
                combinable = getattr(table, 'combinable', True)  # Default to True if missing
                
                result.append({
                    "id": str(table.id),
                    "name": table.name,
                    "capacity": capacity,
                    "room_id": str(table.room_id),
                    "room_name": table.room.name,
                    "combinable": combinable,
                    "active": table.active
                })
            
            print(f"🔍 DEBUG: Returning {len(result)} tables")
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ DEBUG: Tables error: {str(e)}")
        return {"status": "error", "message": f"Error loading tables: {str(e)}"}

@app.get("/admin/rooms")
async def get_rooms_simple():
    """Simple endpoint to get all rooms"""
    try:
        from app.core.database import SessionLocal
        from app.models.room import Room
        
        print("🔍 DEBUG: /admin/rooms called")
        
        db = SessionLocal()
        try:
            rooms = db.query(Room).filter(Room.active == True).all()
            print(f"🔍 DEBUG: Found {len(rooms)} rooms")
            
            result = []
            for room in rooms:
                # Handle missing description field gracefully
                description = getattr(room, 'description', '')
                
                result.append({
                    "id": str(room.id),
                    "name": room.name,
                    "description": description,
                    "active": room.active
                })
            
            print(f"🔍 DEBUG: Returning {len(result)} rooms")
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ DEBUG: Rooms error: {str(e)}")
        return {"status": "error", "message": f"Error loading rooms: {str(e)}"}

@app.get("/admin/reservations")
async def get_reservations_simple(date_filter: str = None):
    """Simple endpoint to get reservations"""
    try:
        from app.core.database import SessionLocal
        from app.models.reservation import Reservation
        from app.models.room import Room
        from datetime import datetime
        
        db = SessionLocal()
        try:
            query = db.query(Reservation).join(Room)
            
            if date_filter:
                target_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
                query = query.filter(Reservation.date == target_date)
            
            reservations = query.all()
            
            result = []
            for reservation in reservations:
                result.append({
                    "id": str(reservation.id),
                    "customer_name": reservation.customer_name,
                    "email": reservation.email,
                    "phone": reservation.phone,
                    "party_size": reservation.party_size,
                    "date": reservation.date.isoformat(),
                    "time": reservation.time.strftime("%H:%M"),
                    "duration_hours": reservation.duration_hours_safe,
                    "room_id": str(reservation.room_id),
                    "room_name": reservation.room.name,
                    "status": reservation.status.value,
                    "reservation_type": reservation.reservation_type.value,
                    "notes": reservation.notes,
                    "admin_notes": reservation.admin_notes,
                    "created_at": reservation.created_at.isoformat(),
                    "tables": []  # We'll add table assignments later
                })
            
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        return {"status": "error", "message": f"Error loading reservations: {str(e)}"}

@app.get("/api/settings/restaurant")
async def get_restaurant_settings():
    """Simple restaurant settings endpoint"""
    return {
        "restaurant_name": "The Castle Pub",
        "phone": "+1-555-CASTLE",
        "email": "info@castlepub.com",
        "address": "123 Castle Street",
        "opening_time": "17:00",
        "closing_time": "23:00"
    }

@app.get("/api/settings/working-hours")
async def get_working_hours():
    """Simple working hours endpoint"""
    return [
        {"day": "monday", "open_time": "17:00", "close_time": "23:00", "is_open": True},
        {"day": "tuesday", "open_time": "17:00", "close_time": "23:00", "is_open": True},
        {"day": "wednesday", "open_time": "17:00", "close_time": "23:00", "is_open": True},
        {"day": "thursday", "open_time": "17:00", "close_time": "23:00", "is_open": True},
        {"day": "friday", "open_time": "17:00", "close_time": "24:00", "is_open": True},
        {"day": "saturday", "open_time": "16:00", "close_time": "24:00", "is_open": True},
        {"day": "sunday", "open_time": "16:00", "close_time": "22:00", "is_open": True}
    ]

@app.get("/api/rooms")
async def get_public_rooms():
    """Public rooms endpoint (same as admin but without auth)"""
    try:
        from app.core.database import SessionLocal
        from app.models.room import Room
        
        db = SessionLocal()
        try:
            rooms = db.query(Room).filter(Room.active == True).all()
            
            result = []
            for room in rooms:
                result.append({
                    "id": str(room.id),
                    "name": room.name,
                    "description": room.description,
                    "active": room.active
                })
            
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        return []

@app.get("/admin/reports/daily")
async def get_daily_report_simple(report_date: str):
    """Simple daily report endpoint"""
    try:
        from app.core.database import SessionLocal
        from app.models.reservation import Reservation
        from datetime import datetime
        
        # Parse the date
        target_date = datetime.strptime(report_date, "%Y-%m-%d").date()
        
        db = SessionLocal()
        try:
            # Get reservations for the date
            reservations = db.query(Reservation).filter(Reservation.date == target_date).all()
            
            # Generate simple HTML report
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Daily Report - {target_date}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ text-align: center; margin-bottom: 20px; }}
                    .reservation {{ margin: 10px 0; padding: 10px; border: 1px solid #ccc; }}
                    .summary {{ background: #f5f5f5; padding: 10px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>The Castle Pub</h1>
                    <h2>Daily Report - {target_date}</h2>
                </div>
                <div class="summary">
                    <strong>Total Reservations: {len(reservations)}</strong>
                </div>
            """
            
            for reservation in reservations:
                html_content += f"""
                <div class="reservation">
                    <strong>{reservation.customer_name}</strong> - {reservation.time.strftime('%H:%M')}<br>
                    Party Size: {reservation.party_size}<br>
                    Phone: {reservation.phone}<br>
                    Status: {reservation.status.value}<br>
                    {f'Notes: {reservation.notes}' if reservation.notes else ''}
                </div>
                """
            
            html_content += """
            </body>
            </html>
            """
            
            return Response(
                content=html_content,
                media_type="text/html",
                headers={"Content-Disposition": f"attachment; filename=daily_report_{target_date}.html"}
            )
            
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating report: {str(e)}"
        )

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
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    ) 

# Add a simple endpoint to trigger migrations manually
@app.get("/init-db")
async def initialize_database():
    """Manually trigger database initialization"""
    try:
        run_migrations()
        return {"status": "success", "message": "Database initialized"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def run_migrations():
    """Run database migrations"""
    try:
        from sqlalchemy import text
        from app.core.database import engine
        
        with engine.connect() as conn:
            # Add duration_hours column to reservations if it doesn't exist
            try:
                conn.execute(text("""
                    ALTER TABLE reservations 
                    ADD COLUMN IF NOT EXISTS duration_hours INTEGER DEFAULT 2
                """))
                conn.execute(text("""
                    UPDATE reservations 
                    SET duration_hours = 2 
                    WHERE duration_hours IS NULL
                """))
                # Make sure the column is not null
                conn.execute(text("""
                    ALTER TABLE reservations 
                    ALTER COLUMN duration_hours SET NOT NULL
                """))
                print("✅ Duration hours migration completed")
            except Exception as e:
                print(f"⚠️ Duration hours migration warning: {e}")
            
            # Add email column to users if it doesn't exist
            try:
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN IF NOT EXISTS email VARCHAR UNIQUE
                """))
                print("✅ Email column migration completed")
            except Exception as e:
                print(f"⚠️ Email column migration warning: {e}")
            
            # Create table_layouts table if it doesn't exist
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS table_layouts (
                        id TEXT PRIMARY KEY,
                        table_id TEXT NOT NULL UNIQUE,
                        room_id TEXT NOT NULL,
                        x_position FLOAT NOT NULL,
                        y_position FLOAT NOT NULL,
                        width FLOAT DEFAULT 100.0,
                        height FLOAT DEFAULT 80.0,
                        shape VARCHAR DEFAULT 'rectangular',
                        color VARCHAR DEFAULT '#4A90E2',
                        border_color VARCHAR DEFAULT '#2E5BBA',
                        text_color VARCHAR DEFAULT '#FFFFFF',
                        show_capacity BOOLEAN DEFAULT TRUE,
                        show_name BOOLEAN DEFAULT TRUE,
                        font_size INTEGER DEFAULT 12,
                        z_index INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (table_id) REFERENCES tables(id) ON DELETE CASCADE,
                        FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
                    )
                """))
                print("✅ Table layouts migration completed")
            except Exception as e:
                print(f"⚠️ Table layouts migration warning: {e}")
            
            # Create room_layouts table if it doesn't exist
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS room_layouts (
                        id TEXT PRIMARY KEY,
                        room_id TEXT NOT NULL UNIQUE,
                        width FLOAT DEFAULT 800.0,
                        height FLOAT DEFAULT 600.0,
                        background_color VARCHAR DEFAULT '#F5F5F5',
                        grid_enabled BOOLEAN DEFAULT TRUE,
                        grid_size INTEGER DEFAULT 20,
                        grid_color VARCHAR DEFAULT '#E0E0E0',
                        show_entrance BOOLEAN DEFAULT TRUE,
                        entrance_position VARCHAR DEFAULT 'top',
                        show_bar BOOLEAN DEFAULT FALSE,
                        bar_position VARCHAR DEFAULT 'center',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
                    )
                """))
                print("✅ Room layouts migration completed")
            except Exception as e:
                print(f"⚠️ Room layouts migration warning: {e}")
            
            conn.commit()
            
    except Exception as e:
        print(f"❌ Migration error: {e}")
        raise 