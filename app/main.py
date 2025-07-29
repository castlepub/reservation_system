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
app.include_router(auth.router)
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

@app.get("/")
async def root():
    """Serve the main HTML page"""
    logger.info(f"🏠 Root endpoint called!")
    index_path = os.path.join(static_dir, "index.html")
    
    if os.path.exists(index_path):
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            from fastapi.responses import HTMLResponse
            return HTMLResponse(content=html_content)
        except Exception as e:
            logger.error(f"Error reading index.html: {str(e)}")
            return {
                "message": "The Castle Pub Reservation System",
                "status": "running",
                "version": "1.0.0",
                "docs": "/docs",
                "error": f"Could not load frontend: {str(e)}"
            }
    else:
        return {
            "message": "The Castle Pub Reservation System",
            "status": "running",
            "version": "1.0.0",
            "docs": "/docs",
            "note": "Frontend not found, API is available"
        }

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
        "docs": "/docs",
        "status": "running"
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
    from sqlalchemy import text
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Check if duration_hours column exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='reservations' AND column_name='duration_hours'
        """)).fetchone()
        
        if not result:
            print("🔄 Adding duration_hours column to reservations table...")
            db.execute(text("ALTER TABLE reservations ADD COLUMN duration_hours INTEGER DEFAULT 2 NOT NULL"))
            db.commit()
            print("✅ duration_hours column added successfully")
        else:
            print("✅ duration_hours column already exists")
        
        # Update existing reservations
        db.execute(text("UPDATE reservations SET duration_hours = 2 WHERE duration_hours IS NULL"))
        db.commit()
        print("✅ All existing reservations updated with default duration")
        
        # Check if layout tables exist
        try:
            db.execute(text("SELECT 1 FROM table_layouts LIMIT 1"))
            print("✅ table_layouts table exists")
        except Exception:
            print("🔄 Creating table_layouts table...")
            db.execute(text("""
                CREATE TABLE table_layouts (
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
                    updated_at TIMESTAMP
                )
            """))
            db.commit()
            print("✅ table_layouts table created")
        
        try:
            db.execute(text("SELECT 1 FROM room_layouts LIMIT 1"))
            print("✅ room_layouts table exists")
        except Exception:
            print("🔄 Creating room_layouts table...")
            db.execute(text("""
                CREATE TABLE room_layouts (
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
                    updated_at TIMESTAMP
                )
            """))
            db.commit()
            print("✅ room_layouts table created")
        
    except Exception as e:
        print(f"⚠️ Migration error: {e}")
        db.rollback()
        raise
    finally:
        db.close() 