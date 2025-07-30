from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.database import engine, Base
from app.api import auth, public, admin
# from app.api.layout import router as layout_router  # Keep commented out for now
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
# app.include_router(layout_router)  # Keep commented out for now

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
                    ADD COLUMN IF NOT EXISTS duration_hours INTEGER DEFAULT 2 NOT NULL
                """))
                conn.execute(text("""
                    UPDATE reservations 
                    SET duration_hours = 2 
                    WHERE duration_hours IS NULL
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