from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
# from app.core.database import engine, Base  # Comment out for now
# from app.api import auth, public, admin  # Comment out for now
# from app.core.config import settings  # Comment out for now
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