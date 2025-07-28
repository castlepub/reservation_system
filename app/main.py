from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.database import engine, Base
from app.api import auth, public, admin
from app.core.config import settings
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="The Castle Pub Reservation System",
    description="A comprehensive restaurant reservation system for The Castle Pub",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        # Create database tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Test database connection
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection test successful")
        
        # Create admin user if it doesn't exist
        from app.core.database import SessionLocal
        from app.core.security import get_password_hash
        from app.models.user import User, UserRole
        from app.models.reservation import ReservationType
        from app.models.settings import WorkingHours, DayOfWeek, RestaurantSettings
        from sqlalchemy import text
        from datetime import time
        
        db = SessionLocal()
        try:
            # Add missing columns to existing tables if they don't exist
            try:
                # Check if reservation_type column exists, if not add it
                db.execute(text("SELECT reservation_type FROM reservations LIMIT 1"))
            except Exception:
                logger.info("Adding reservation_type column to reservations table")
                db.execute(text("ALTER TABLE reservations ADD COLUMN reservation_type VARCHAR DEFAULT 'dining'"))
                db.commit()
            
            try:
                # Check if admin_notes column exists, if not add it
                db.execute(text("SELECT admin_notes FROM reservations LIMIT 1"))
            except Exception:
                logger.info("Adding admin_notes column to reservations table")
                db.execute(text("ALTER TABLE reservations ADD COLUMN admin_notes TEXT"))
                db.commit()
            
            # Update existing reservations to have default reservation_type
            try:
                db.execute(text("UPDATE reservations SET reservation_type = 'dining' WHERE reservation_type IS NULL"))
                db.commit()
            except Exception:
                pass
            
            admin_user = db.query(User).filter(User.username == "admin").first()
            if not admin_user:
                admin_user = User(
                    username="admin",
                    password_hash=get_password_hash("admin123"),
                    role=UserRole.ADMIN
                )
                db.add(admin_user)
                db.commit()
                logger.info("✅ Admin user created (username: admin, password: admin123)")
            else:
                logger.info("✅ Admin user already exists")
                
            logger.info("✅ Database schema updated successfully")
        except Exception as e:
            logger.error(f"Database schema update error: {e}")
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise e

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
app.include_router(public.router)
app.include_router(admin.router, prefix="/api")

# Import and include dashboard router
from app.api import dashboard
app.include_router(dashboard.router, prefix="/api")

# Import and include settings router
from app.api import settings
app.include_router(settings.router, prefix="/api")

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

@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {
        "message": "The Castle Pub Reservation System API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    try:
        # Test database connection
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
        
        return {
            "status": "healthy", 
            "service": "reservation-system",
            "database": "connected",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        # Return 200 even if database fails, but indicate the issue
        return {
            "status": "degraded",
            "service": "reservation-system", 
            "database": "disconnected",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }

@app.get("/health/simple")
async def simple_health_check():
    """Simple health check that doesn't test database"""
    return {
        "status": "healthy",
        "service": "reservation-system",
        "message": "Service is running",
        "version": "1.0.0"
    }

@app.get("/ping")
async def ping():
    """Ultra simple ping endpoint"""
    return {"pong": "ok"}

@app.get("/debug")
async def debug():
    """Debug endpoint to check Railway configuration"""
    import os
    return {
        "port": os.getenv('PORT', 'NOT_SET'),
        "railway_environment": os.getenv('RAILWAY_ENVIRONMENT', 'NOT_SET'),
        "railway_service_name": os.getenv('RAILWAY_SERVICE_NAME', 'NOT_SET'),
        "current_dir": os.getcwd(),
        "static_dir_exists": os.path.exists(static_dir),
        "static_dir_path": static_dir
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler for unexpected errors"""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 