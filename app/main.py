import os
from datetime import datetime, date, time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Import routers - testing one by one
try:
    from app.api.auth import router as auth_router
    print("✅ Auth router imported successfully")
except Exception as e:
    print(f"❌ Auth router failed: {e}")
    auth_router = None

try:
    from app.api.admin import router as admin_router
    print("✅ Admin router imported successfully")
except Exception as e:
    print(f"❌ Admin router failed: {e}")
    admin_router = None

try:
    from app.api.settings import router as settings_router
    print("✅ Settings router imported successfully")
except Exception as e:
    print(f"❌ Settings router failed: {e}")
    settings_router = None

try:
    from app.api.public import router as public_router
    print("✅ Public router imported successfully")
except Exception as e:
    print(f"❌ Public router failed: {e}")
    public_router = None

try:
    from app.api.dashboard import router as dashboard_router
    print("✅ Dashboard router imported successfully")
except Exception as e:
    print(f"❌ Dashboard router failed: {e}")
    dashboard_router = None

try:
    from app.api.layout import router as layout_router
    print("✅ Layout router imported successfully")
except Exception as e:
    print(f"❌ Layout router failed: {e}")
    layout_router = None

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

# Include routers - only if they imported successfully
if auth_router:
    app.include_router(auth_router, prefix="/api")
    print("✅ Auth router included")

if admin_router:
    app.include_router(admin_router)
    print("✅ Admin router included")

if settings_router:
    app.include_router(settings_router, prefix="/api")
    print("✅ Settings router included")

if public_router:
    app.include_router(public_router, prefix="/api")
    print("✅ Public router included")

if dashboard_router:
    app.include_router(dashboard_router, prefix="/api")
    print("✅ Dashboard router included")

if layout_router:
    app.include_router(layout_router, prefix="/api/layout")
    print("✅ Layout router included")

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

@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {"message": "The Castle Pub Reservation System API", "status": "running"}

@app.get("/api/debug/db-test")
async def test_database_connection():
    """Test database connection without dependencies"""
    try:
        from app.core.database import get_db
        from sqlalchemy.orm import Session
        
        # Try to get a database session
        db_gen = get_db()
        db = next(db_gen)
        
        # Try a simple query
        from sqlalchemy import text
        result = db.execute(text("SELECT 1 as test"))
        test_result = result.fetchone()
        
        return {
            "status": "success",
            "message": "Database connection working",
            "test_query_result": test_result.test if test_result else None
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Database connection failed: {str(e)}",
            "error_type": type(e).__name__
        }

@app.get("/api/setup-database")
async def setup_database():
    """Set up database tables if they don't exist"""
    try:
        from app.core.database import engine
        from app.models import user, room, table, reservation
        from sqlalchemy import text
        
        # Test connection first
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Database connection working!")
            
            # Create all tables in public schema
            from app.core.database import Base
            Base.metadata.create_all(bind=engine)
            print("✅ Database tables created!")
            
            # Ensure we're using the public schema
            connection.execute(text("SET search_path TO public"))
            print("✅ Schema set to public")
            
            # Test if we can query tables
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            print(f"✅ Found {len(tables)} tables: {tables}")
            
            return {
                "status": "success",
                "message": "Database setup completed",
                "tables": tables
            }
            
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Database setup failed: {str(e)}",
            "error_type": type(e).__name__
        }

@app.get("/api/debug/check-tables")
async def check_tables():
    """Check table structure and schema"""
    try:
        from app.core.database import engine
        from sqlalchemy import text
        
        with engine.connect() as connection:
            # Check current schema
            result = connection.execute(text("SELECT current_schema()"))
            current_schema = result.fetchone()[0]
            
            # Check tables in current schema
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = current_schema()
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            
            # Check if users table exists specifically
            result = connection.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = current_schema() 
                    AND table_name = 'users'
                )
            """))
            users_exists = result.fetchone()[0]
            
            return {
                "status": "success",
                "current_schema": current_schema,
                "tables": tables,
                "users_table_exists": users_exists,
                "total_tables": len(tables)
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to check tables: {str(e)}",
            "error_type": type(e).__name__
        }

@app.post("/api/create-admin")
async def create_admin_user():
    """Create a default admin user"""
    try:
        from app.core.database import SessionLocal
        from app.models.user import User, UserRole
        from app.core.security import get_password_hash
        
        db = SessionLocal()
        
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            return {
                "status": "error",
                "message": "Admin user already exists"
            }
        
        # Create admin user
        admin_user = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            email="admin@thecastle.de"
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        db.close()
        
        return {
            "status": "success",
            "message": "Admin user created successfully",
            "username": "admin",
            "password": "admin123"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to create admin user: {str(e)}",
            "error_type": type(e).__name__
        }

@app.post("/api/init-database")
async def initialize_database():
    """Initialize database with correct data"""
    try:
        from app.core.database import SessionLocal
        from app.models.user import User, UserRole
        from app.models.room import Room
        from app.models.table import Table
        from app.models.settings import Settings
        from app.models.working_hours import WorkingHours
        from app.core.security import get_password_hash
        
        db = SessionLocal()
        
        # Create admin user
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if not existing_admin:
            admin_user = User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                email="admin@thecastle.de"
            )
            db.add(admin_user)
            print("✅ Admin user created")
        
        # Create rooms with correct names
        rooms_data = [
            {"name": "Front Room", "description": "Front dining area", "table_count": 6},
            {"name": "Middle Room", "description": "Middle dining area", "table_count": 6},
            {"name": "Back Room", "description": "Back dining area", "table_count": 6},
            {"name": "Biergarden", "description": "Outdoor beer garden", "table_count": 12}
        ]
        
        for room_data in rooms_data:
            existing_room = db.query(Room).filter(Room.name == room_data["name"]).first()
            if not existing_room:
                room = Room(
                    name=room_data["name"],
                    description=room_data["description"],
                    active=True
                )
                db.add(room)
                db.commit()
                db.refresh(room)
                print(f"✅ Room created: {room.name}")
                
                # Create tables for this room
                table_count = room_data["table_count"]
                for i in range(1, table_count + 1):
                    table = Table(
                        name=f"{room.name[:2]}{i}",  # FR1, FR2, etc.
                        capacity=4,  # Default capacity
                        room_id=room.id,
                        active=True
                    )
                    db.add(table)
                print(f"✅ Created {table_count} tables for {room.name}")
        
        # Settings will be created later if needed
        
        # Create working hours with correct schedule
        working_hours_data = [
            {"day": "MONDAY", "open": "15:00", "close": "01:00"},
            {"day": "TUESDAY", "open": "15:00", "close": "01:00"},
            {"day": "WEDNESDAY", "open": "15:00", "close": "01:00"},
            {"day": "THURSDAY", "open": "15:00", "close": "01:00"},
            {"day": "FRIDAY", "open": "15:00", "close": "02:00"},
            {"day": "SATURDAY", "open": "13:00", "close": "02:00"},
            {"day": "SUNDAY", "open": "13:00", "close": "01:00"}
        ]
        
        for wh_data in working_hours_data:
            existing_wh = db.query(WorkingHours).filter(WorkingHours.day_of_week == wh_data["day"]).first()
            if not existing_wh:
                wh = WorkingHours(
                    day_of_week=wh_data["day"],
                    is_open=True,
                    open_time=wh_data["open"],
                    close_time=wh_data["close"]
                )
                db.add(wh)
                print(f"✅ Working hours created for {wh_data['day']}: {wh_data['open']}-{wh_data['close']}")
        
        db.commit()
        db.close()
        
        return {
            "status": "success",
            "message": "Database initialized with correct data",
            "admin_credentials": {
                "username": "admin",
                "password": "admin123"
            },
            "rooms_created": [room["name"] for room in rooms_data],
            "working_hours": "Mon-Thu: 15:00-01:00, Fri: 15:00-02:00, Sat: 13:00-02:00, Sun: 13:00-01:00"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to initialize database: {str(e)}",
            "error_type": type(e).__name__
        }

@app.get("/api/debug/check-data")
async def check_database_data():
    """Check what data exists in the database"""
    try:
        from app.core.database import SessionLocal
        from app.models.user import User
        from app.models.room import Room
        from app.models.table import Table
        from app.models.reservation import Reservation
        from app.models.settings import Settings
        from app.models.working_hours import WorkingHours
        
        db = SessionLocal()
        
        # Count records in each table
        user_count = db.query(User).count()
        room_count = db.query(Room).count()
        table_count = db.query(Table).count()
        reservation_count = db.query(Reservation).count()
        settings_count = db.query(Settings).count()
        working_hours_count = db.query(WorkingHours).count()
        
        # Get some sample data
        users = db.query(User).limit(3).all()
        rooms = db.query(Room).limit(3).all()
        reservations = db.query(Reservation).limit(3).all()
        
        db.close()
        
        return {
            "status": "success",
            "counts": {
                "users": user_count,
                "rooms": room_count,
                "tables": table_count,
                "reservations": reservation_count,
                "settings": settings_count,
                "working_hours": working_hours_count
            },
            "sample_users": [{"username": u.username, "role": u.role.value} for u in users],
            "sample_rooms": [{"name": r.name, "active": r.active} for r in rooms],
            "sample_reservations": [{"id": str(r.id), "guest_name": r.guest_name} for r in reservations]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to check data: {str(e)}",
            "error_type": type(e).__name__
        }

@app.post("/api/simple-init")
async def simple_initialize():
    """Simple database initialization without problematic imports"""
    try:
        from app.core.database import SessionLocal
        from app.models.user import User, UserRole
        from app.models.room import Room
        from app.models.table import Table
        from app.core.security import get_password_hash
        
        db = SessionLocal()
        
        # Create admin user
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if not existing_admin:
            admin_user = User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                email="admin@thecastle.de"
            )
            db.add(admin_user)
            print("✅ Admin user created")
        
        # Create rooms with correct names
        rooms_data = [
            {"name": "Front Room", "description": "Front dining area", "table_count": 6},
            {"name": "Middle Room", "description": "Middle dining area", "table_count": 6},
            {"name": "Back Room", "description": "Back dining area", "table_count": 6},
            {"name": "Biergarden", "description": "Outdoor beer garden", "table_count": 12}
        ]
        
        for room_data in rooms_data:
            existing_room = db.query(Room).filter(Room.name == room_data["name"]).first()
            if not existing_room:
                room = Room(
                    name=room_data["name"],
                    description=room_data["description"],
                    active=True
                )
                db.add(room)
                db.commit()
                db.refresh(room)
                print(f"✅ Room created: {room.name}")
                
                # Create tables for this room
                table_count = room_data["table_count"]
                for i in range(1, table_count + 1):
                    table = Table(
                        name=f"{room.name[:2]}{i}",  # FR1, FR2, etc.
                        capacity=4,  # Default capacity
                        room_id=room.id,
                        active=True
                    )
                    db.add(table)
                print(f"✅ Created {table_count} tables for {room.name}")
        
        db.commit()
        db.close()
        
        return {
            "status": "success",
            "message": "Database initialized with admin user and rooms",
            "admin_credentials": {
                "username": "admin",
                "password": "admin123"
            },
            "rooms_created": [room["name"] for room in rooms_data]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to initialize database: {str(e)}",
            "error_type": type(e).__name__
        }

@app.post("/api/create-working-hours")
async def create_working_hours():
    """Create working hours with correct schedule"""
    try:
        from app.core.database import SessionLocal
        from app.models.settings import WorkingHours
        
        db = SessionLocal()
        
        # Create working hours with correct schedule
        working_hours_data = [
            {"day": "MONDAY", "open": "15:00", "close": "01:00"},
            {"day": "TUESDAY", "open": "15:00", "close": "01:00"},
            {"day": "WEDNESDAY", "open": "15:00", "close": "01:00"},
            {"day": "THURSDAY", "open": "15:00", "close": "01:00"},
            {"day": "FRIDAY", "open": "15:00", "close": "02:00"},
            {"day": "SATURDAY", "open": "13:00", "close": "02:00"},
            {"day": "SUNDAY", "open": "13:00", "close": "01:00"}
        ]
        
        created_count = 0
        for wh_data in working_hours_data:
            existing_wh = db.query(WorkingHours).filter(WorkingHours.day_of_week == wh_data["day"]).first()
            if not existing_wh:
                wh = WorkingHours(
                    day_of_week=wh_data["day"],
                    is_open=True,
                    open_time=wh_data["open"],
                    close_time=wh_data["close"]
                )
                db.add(wh)
                created_count += 1
                print(f"✅ Working hours created for {wh_data['day']}: {wh_data['open']}-{wh_data['close']}")
        
        db.commit()
        db.close()
        
        return {
            "status": "success",
            "message": f"Created {created_count} working hours entries",
            "working_hours": "Mon-Thu: 15:00-01:00, Fri: 15:00-02:00, Sat: 13:00-02:00, Sun: 13:00-01:00"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to create working hours: {str(e)}",
            "error_type": type(e).__name__
        }

@app.post("/api/update-working-hours")
async def update_working_hours_schedule():
    """Update working hours with correct schedule"""
    try:
        from app.core.database import SessionLocal
        from app.models.settings import WorkingHours
        
        db = SessionLocal()
        
        # Update working hours with correct schedule
        working_hours_data = [
            {"day": "MONDAY", "open": "15:00", "close": "01:00"},
            {"day": "TUESDAY", "open": "15:00", "close": "01:00"},
            {"day": "WEDNESDAY", "open": "15:00", "close": "01:00"},
            {"day": "THURSDAY", "open": "15:00", "close": "01:00"},
            {"day": "FRIDAY", "open": "15:00", "close": "02:00"},
            {"day": "SATURDAY", "open": "13:00", "close": "02:00"},
            {"day": "SUNDAY", "open": "13:00", "close": "01:00"}
        ]
        
        updated_count = 0
        for wh_data in working_hours_data:
            existing_wh = db.query(WorkingHours).filter(WorkingHours.day_of_week == wh_data["day"]).first()
            if existing_wh:
                existing_wh.open_time = wh_data["open"]
                existing_wh.close_time = wh_data["close"]
                existing_wh.is_open = True
                updated_count += 1
                print(f"✅ Updated working hours for {wh_data['day']}: {wh_data['open']}-{wh_data['close']}")
            else:
                wh = WorkingHours(
                    day_of_week=wh_data["day"],
                    is_open=True,
                    open_time=wh_data["open"],
                    close_time=wh_data["close"]
                )
                db.add(wh)
                updated_count += 1
                print(f"✅ Created working hours for {wh_data['day']}: {wh_data['open']}-{wh_data['close']}")
        
        db.commit()
        db.close()
        
        return {
            "status": "success",
            "message": f"Updated {updated_count} working hours entries",
            "working_hours": "Mon-Thu: 15:00-01:00, Fri: 15:00-02:00, Sat: 13:00-02:00, Sun: 13:00-01:00"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to update working hours: {str(e)}",
            "error_type": type(e).__name__
        }



@app.post("/api/cleanup-duplicates")
async def cleanup_duplicate_reservations():
    """Clean up duplicate reservations, keeping only the first one for each customer/date/time"""
    try:
        from app.core.database import SessionLocal
        from app.models.reservation import Reservation
        from sqlalchemy import func
        
        db = SessionLocal()
        
        # Get all reservations
        all_reservations = db.query(Reservation).all()
        
        # Group by customer_name, date, time
        grouped = {}
        for res in all_reservations:
            key = (res.customer_name, res.date, res.time)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(res)
        
        # Find duplicates and delete them
        deleted_count = 0
        for key, reservations in grouped.items():
            if len(reservations) > 1:
                # Sort by created_at to keep the oldest one
                reservations.sort(key=lambda x: x.created_at)
                
                # Delete all except the first one
                for res in reservations[1:]:
                    db.delete(res)
                    deleted_count += 1
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Cleaned up {deleted_count} duplicate reservations",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to cleanup duplicates: {str(e)}",
            "error_type": type(e).__name__
        }
    finally:
        db.close()

@app.post("/api/assign-tables-to-existing")
async def assign_tables_to_existing_reservations():
    """Assign tables to existing reservations that don't have table assignments"""
    try:
        from app.core.database import SessionLocal
        from app.models.reservation import Reservation, ReservationTable
        from app.models.table import Table
        from app.services.table_service import TableService
        
        db = SessionLocal()
        table_service = TableService(db)
        
        # Get all reservations without table assignments
        reservations_without_tables = []
        all_reservations = db.query(Reservation).all()
        
        for reservation in all_reservations:
            table_assignments = db.query(ReservationTable).filter(
                ReservationTable.reservation_id == reservation.id
            ).all()
            
            if not table_assignments:
                reservations_without_tables.append(reservation)
        
        assigned_count = 0
        for reservation in reservations_without_tables:
            # Find available tables for this reservation
            table_combo = table_service.find_best_table_combination(
                reservation.room_id,
                reservation.date,
                reservation.time,
                reservation.party_size
            )
            
            if table_combo:
                # Assign tables
                table_ids = [str(table.id) for table in table_combo]
                table_service.assign_tables_to_reservation(str(reservation.id), table_ids)
                assigned_count += 1
                print(f"✅ Assigned tables to reservation {reservation.customer_name}")
            else:
                print(f"❌ No tables available for reservation {reservation.customer_name}")
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Assigned tables to {assigned_count} reservations",
            "assigned_count": assigned_count,
            "total_without_tables": len(reservations_without_tables)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to assign tables: {str(e)}",
            "error_type": type(e).__name__
        }
    finally:
        db.close()

@app.post("/api/debug-table-assignment")
async def debug_table_assignment():
    """Debug table assignment step by step"""
    try:
        from app.core.database import SessionLocal
        from app.models.room import Room
        from app.models.table import Table
        from app.models.reservation import Reservation, ReservationTable
        from app.services.table_service import TableService
        from datetime import date, time
        
        db = SessionLocal()
        table_service = TableService(db)
        
        # Get first room
        room = db.query(Room).filter(Room.active == True).first()
        if not room:
            return {"error": "No active rooms found"}
        
        # Get all tables in this room
        tables = db.query(Table).filter(Table.room_id == room.id).all()
        
        # Get all reservations for today
        today = date(2025, 8, 8)
        reservations = db.query(Reservation).filter(Reservation.date == today).all()
        
        # Get table assignments for today
        table_assignments = db.query(ReservationTable).join(Reservation).filter(Reservation.date == today).all()
        
        # Test table combination finding
        test_time = time(18, 0)
        table_combo = table_service.find_best_table_combination(
            room.id,
            today,
            test_time,
            4
        )
        
        return {
            "status": "success",
            "room": {
                "id": str(room.id),
                "name": room.name
            },
            "tables_in_room": len(tables),
            "reservations_today": len(reservations),
            "table_assignments_today": len(table_assignments),
            "test_table_combo_found": table_combo is not None,
            "test_table_combo_count": len(table_combo) if table_combo else 0,
            "test_table_combo": [{"id": str(t.id), "name": t.name, "capacity": t.capacity} for t in table_combo] if table_combo else None
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Debug failed: {str(e)}",
            "error_type": type(e).__name__
        }
    finally:
        db.close()

@app.post("/api/debug-reservation-creation")
async def debug_reservation_creation():
    """Debug reservation creation step by step"""
    try:
        from app.core.database import SessionLocal
        from app.models.room import Room
        from app.models.table import Table
        from app.models.reservation import Reservation, ReservationTable
        from app.services.table_service import TableService
        from app.services.reservation_service import ReservationService
        from app.schemas.reservation import ReservationCreate
        from datetime import date, time
        
        db = SessionLocal()
        table_service = TableService(db)
        reservation_service = ReservationService(db)
        
        # Get first room
        room = db.query(Room).filter(Room.active == True).first()
        if not room:
            return {"error": "No active rooms found"}
        
        # Create test reservation data
        test_data = ReservationCreate(
            customer_name="Debug Test",
            email="debug@test.com",
            phone="1234567890",
            party_size=4,
            date=date(2025, 8, 8),
            time=time(18, 0),
            duration_hours=2,
            room_id=room.id,
            reservation_type="dining",
            notes="Debug test"
        )
        
        debug_steps = []
        
        # Step 1: Validate reservation request
        try:
            reservation_service._validate_reservation_request(test_data)
            debug_steps.append("✅ Step 1: Validation passed")
        except Exception as e:
            debug_steps.append(f"❌ Step 1: Validation failed - {str(e)}")
            return {"debug_steps": debug_steps}
        
        # Step 2: Find optimal room
        try:
            optimal_room_id = reservation_service._find_optimal_room_for_reservation(test_data)
            debug_steps.append(f"✅ Step 2: Optimal room found - {optimal_room_id}")
        except Exception as e:
            debug_steps.append(f"❌ Step 2: Optimal room failed - {str(e)}")
            return {"debug_steps": debug_steps}
        
        # Step 3: Find table combination
        try:
            table_combo = table_service.find_best_table_combination(
                optimal_room_id,
                test_data.date,
                test_data.time,
                test_data.party_size
            )
            if table_combo:
                debug_steps.append(f"✅ Step 3: Table combo found - {len(table_combo)} tables")
            else:
                debug_steps.append("❌ Step 3: No table combo found")
                return {"debug_steps": debug_steps}
        except Exception as e:
            debug_steps.append(f"❌ Step 3: Table combo failed - {str(e)}")
            return {"debug_steps": debug_steps}
        
        # Step 4: Create reservation object
        try:
            actual_room_id = table_combo[0].room_id
            reservation = Reservation(
                customer_name=test_data.customer_name,
                email=test_data.email,
                phone=test_data.phone,
                party_size=test_data.party_size,
                date=test_data.date,
                time=test_data.time,
                room_id=actual_room_id,
                reservation_type=test_data.reservation_type,
                notes=test_data.notes
            )
            debug_steps.append("✅ Step 4: Reservation object created")
        except Exception as e:
            debug_steps.append(f"❌ Step 4: Reservation object failed - {str(e)}")
            return {"debug_steps": debug_steps}
        
        # Step 5: Add to database
        try:
            db.add(reservation)
            db.flush()
            debug_steps.append(f"✅ Step 5: Reservation added to DB - ID: {reservation.id}")
        except Exception as e:
            debug_steps.append(f"❌ Step 5: Add to DB failed - {str(e)}")
            return {"debug_steps": debug_steps}
        
        # Step 6: Assign tables
        try:
            table_ids = [str(table.id) for table in table_combo]
            table_service.assign_tables_to_reservation(str(reservation.id), table_ids)
            debug_steps.append(f"✅ Step 6: Tables assigned - {len(table_ids)} tables")
        except Exception as e:
            debug_steps.append(f"❌ Step 6: Table assignment failed - {str(e)}")
            return {"debug_steps": debug_steps}
        
        # Step 7: Commit transaction
        try:
            db.commit()
            debug_steps.append("✅ Step 7: Transaction committed")
        except Exception as e:
            debug_steps.append(f"❌ Step 7: Commit failed - {str(e)}")
            return {"debug_steps": debug_steps}
        
        # Step 8: Build response
        try:
            room_name = room.name if room else ""
            table_assignments = [
                {
                    "table_id": str(table.id),
                    "table_name": table.name,
                    "capacity": table.capacity
                } for table in table_combo
            ]
            debug_steps.append("✅ Step 8: Response built successfully")
        except Exception as e:
            debug_steps.append(f"❌ Step 8: Response building failed - {str(e)}")
            return {"debug_steps": debug_steps}
        
        # Clean up - delete the test reservation
        try:
            db.delete(reservation)
            db.commit()
            debug_steps.append("✅ Cleanup: Test reservation deleted")
        except Exception as e:
            debug_steps.append(f"⚠️ Cleanup: Failed to delete test reservation - {str(e)}")
        
        return {
            "status": "success",
            "debug_steps": debug_steps,
            "final_result": "All steps completed successfully"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Debug failed: {str(e)}",
            "error_type": type(e).__name__
        }
    finally:
        db.close()

@app.post("/api/test-reservation-with-schema")
async def test_reservation_with_schema():
    """Test reservation creation with ReservationWithTables schema"""
    try:
        from app.core.database import SessionLocal
        from app.models.room import Room
        from app.models.table import Table
        from app.models.reservation import Reservation, ReservationTable
        from app.services.table_service import TableService
        from app.services.reservation_service import ReservationService
        from app.schemas.reservation import ReservationCreate, ReservationWithTables
        from datetime import date, time
        
        db = SessionLocal()
        table_service = TableService(db)
        reservation_service = ReservationService(db)
        
        # Get first room
        room = db.query(Room).filter(Room.active == True).first()
        if not room:
            return {"error": "No active rooms found"}
        
        # Create test reservation data
        test_data = ReservationCreate(
            customer_name="Schema Test",
            email="schema@test.com",
            phone="1234567890",
            party_size=4,
            date=date(2025, 8, 8),
            time=time(18, 0),
            duration_hours=2,
            room_id=room.id,
            reservation_type="dining",
            notes="Schema test"
        )
        
        # Use the same logic as the actual service
        reservation_service._validate_reservation_request(test_data)
        optimal_room_id = reservation_service._find_optimal_room_for_reservation(test_data)
        table_combo = table_service.find_best_table_combination(
            optimal_room_id,
            test_data.date,
            test_data.time,
            test_data.party_size
        )
        
        if not table_combo:
            return {"error": "No suitable tables available"}
        
        actual_room_id = table_combo[0].room_id
        
        # Create reservation
        reservation = Reservation(
            customer_name=test_data.customer_name,
            email=test_data.email,
            phone=test_data.phone,
            party_size=test_data.party_size,
            date=test_data.date,
            time=test_data.time,
            room_id=actual_room_id,
            reservation_type=test_data.reservation_type,
            notes=test_data.notes
        )
        
        db.add(reservation)
        db.flush()
        
        # Assign tables
        table_ids = [str(table.id) for table in table_combo]
        table_service.assign_tables_to_reservation(str(reservation.id), table_ids)
        
        db.commit()
        
        # Get room name for response
        room = db.query(Room).filter(Room.id == actual_room_id).first()
        
        # Build response with table assignments
        table_assignments = [
            {
                "table_id": str(table.id),
                "table_name": table.name,
                "capacity": table.capacity
            } for table in table_combo
        ]
        
        # Try to create ReservationWithTables
        try:
            result = ReservationWithTables(
                id=str(reservation.id),
                customer_name=reservation.customer_name,
                email=reservation.email,
                phone=reservation.phone,
                party_size=reservation.party_size,
                date=reservation.date,
                time=reservation.time,
                room_id=str(actual_room_id),
                room_name=room.name if room else "",
                status=reservation.status,
                reservation_type=reservation.reservation_type,
                notes=reservation.notes,
                admin_notes=reservation.admin_notes,
                created_at=reservation.created_at,
                updated_at=reservation.updated_at,
                tables=table_assignments
            )
            
            # Clean up
            db.delete(reservation)
            db.commit()
            
            return {
                "status": "success",
                "message": "ReservationWithTables created successfully",
                "reservation": result.dict()
            }
            
        except Exception as e:
            # Clean up
            db.delete(reservation)
            db.commit()
            
            return {
                "status": "error",
                "message": f"ReservationWithTables creation failed: {str(e)}",
                "error_type": type(e).__name__
            }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Test failed: {str(e)}",
            "error_type": type(e).__name__
        }
    finally:
        db.close()