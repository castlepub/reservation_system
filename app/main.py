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

# Mount static files
static_dir = "static"
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    print(f"✓ Static files mounted from: {os.path.abspath(static_dir)}")
else:
    print(f"⚠ Static directory not found: {os.path.abspath(static_dir)}")

@app.get("/")
async def root():
    """Serve the main HTML page"""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)
    else:
        return {
            "message": "The Castle Pub Reservation System API",
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc",
            "note": "Static files not found. Please check the static directory."
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