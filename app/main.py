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
    """Initialize database and run migrations on startup"""
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Run duration migration if needed
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
                
                # Add the column with default value 2
                db.execute(text("ALTER TABLE reservations ADD COLUMN duration_hours INTEGER DEFAULT 2 NOT NULL"))
                db.commit()
                
                print("✅ duration_hours column added successfully")
            else:
                print("✅ duration_hours column already exists")
            
            # Update existing reservations to have duration_hours = 2 if they don't have it
            db.execute(text("UPDATE reservations SET duration_hours = 2 WHERE duration_hours IS NULL"))
            db.commit()
            
            print("✅ All existing reservations updated with default duration")
            
        except Exception as e:
            print(f"⚠️ Migration warning: {e}")
            db.rollback()
        finally:
            db.close()
        
        print("✅ Database initialized successfully")
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        raise

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

# Import and include debug router
# from app.api import debug
# app.include_router(debug.router, prefix="/api")

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