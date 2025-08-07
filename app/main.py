import os
from datetime import datetime
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
    app.include_router(admin_router, prefix="/admin")
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
    """Initialize database with basic data"""
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
        
        # Create default room
        existing_room = db.query(Room).first()
        if not existing_room:
            default_room = Room(
                name="Main Dining Room",
                description="The main dining area",
                active=True
            )
            db.add(default_room)
            db.commit()
            db.refresh(default_room)
            print("✅ Default room created")
            
            # Create some tables
            tables = [
                Table(name="T1", capacity=4, room_id=default_room.id, active=True),
                Table(name="T2", capacity=6, room_id=default_room.id, active=True),
                Table(name="T3", capacity=4, room_id=default_room.id, active=True),
                Table(name="T4", capacity=8, room_id=default_room.id, active=True),
            ]
            for table in tables:
                db.add(table)
            print("✅ Default tables created")
        
        # Create settings
        existing_settings = db.query(Settings).first()
        if not existing_settings:
            settings = Settings(
                restaurant_name="The Castle Pub",
                max_party_size=20,
                min_reservation_hours=0,
                max_reservation_days=90
            )
            db.add(settings)
            print("✅ Settings created")
        
        # Create working hours
        existing_hours = db.query(WorkingHours).first()
        if not existing_hours:
            days = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY']
            for day in days:
                wh = WorkingHours(
                    day_of_week=day,
                    is_open=True,
                    open_time="11:00",
                    close_time="23:00"
                )
                db.add(wh)
            print("✅ Working hours created")
        
        db.commit()
        db.close()
        
        return {
            "status": "success",
            "message": "Database initialized with basic data",
            "admin_credentials": {
                "username": "admin",
                "password": "admin123"
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to initialize database: {str(e)}",
            "error_type": type(e).__name__
        }