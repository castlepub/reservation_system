# GRADUALLY RESTORING FUNCTIONALITY AFTER SUCCESSFUL HEALTH CHECK
import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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

# Basic API endpoints (without database)
@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {"message": "The Castle Pub Reservation System API", "status": "running"}

# Temporary simple endpoints for frontend compatibility
@app.get("/api/rooms")
async def get_rooms_temp():
    """Temporary rooms endpoint"""
    return []

@app.get("/api/dashboard/stats")
async def get_dashboard_stats_temp():
    """Temporary dashboard stats"""
    return {
        "total_reservations_today": 0,
        "total_guests_today": 0,
        "total_reservations_week": 0,
        "total_guests_week": 0,
        "weekly_forecast": [],
        "guest_notes": []
    }

@app.get("/api/dashboard/notes")
async def get_dashboard_notes_temp():
    """Temporary dashboard notes"""
    return []

@app.get("/api/dashboard/customers")
async def get_dashboard_customers_temp():
    """Temporary dashboard customers"""
    return []

@app.get("/api/dashboard/today")
async def get_dashboard_today_temp():
    """Temporary today's reservations"""
    return []

@app.post("/api/auth/login")
async def login_temp():
    """Temporary login endpoint - accepts any credentials"""
    return {
        "access_token": "temporary_token_12345",
        "token_type": "bearer",
        "user": {
            "id": "temp_user",
            "username": "admin",
            "role": "admin"
        }
    }

@app.get("/api/auth/me")
async def get_auth_me_temp():
    """Temporary auth check - always return not authenticated"""
    from fastapi import HTTPException
    raise HTTPException(status_code=401, detail="Not authenticated")

@app.get("/api/settings/restaurant")
async def get_restaurant_settings_temp():
    """Temporary restaurant settings"""
    return {
        "name": "The Castle Pub",
        "address": "123 Castle Street",
        "phone": "+1 234 567 8900",
        "email": "info@castlepub.com",
        "website": "www.castlepub.com"
    }

@app.get("/admin/reservations")
async def get_admin_reservations_temp():
    """Temporary admin reservations"""
    return []

@app.post("/api/reservations")
async def create_reservation_temp():
    """Temporary reservation endpoint"""
    return {"status": "success", "message": "System temporarily in maintenance mode", "id": "temp_reservation_123"}

# All complex endpoints with database dependencies are temporarily disabled