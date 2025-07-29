from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from datetime import datetime, date

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

# Get the correct path to static files
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "..", "static")
static_dir = os.path.abspath(static_dir)

print(f"Static directory path: {static_dir}")
print(f"Static directory exists: {os.path.exists(static_dir)}")

# Mount static files
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    print(f"✅ Static files mounted from: {static_dir}")
else:
    print(f"❌ Static directory not found: {static_dir}")

@app.get("/")
async def root():
    # Serve the HTML file instead of JSON
    html_file = os.path.join(static_dir, "index.html")
    print(f"HTML file path: {html_file}")
    print(f"HTML file exists: {os.path.exists(html_file)}")
    
    if os.path.exists(html_file):
        return FileResponse(html_file)
    else:
        return {"message": "The Castle Pub Reservation System", "status": "running", "error": f"HTML file not found at {html_file}"}

@app.get("/health")
async def health():
    return {"status": "ok", "message": "Service is healthy"}

@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "pong"}

@app.get("/api/test")
async def test_api():
    return {"message": "API is working", "status": "ok"}

# Simple auth endpoints for testing
@app.post("/api/auth/login")
async def login(username: str = Form(...), password: str = Form(...)):
    # For now, just return a simple response
    # In the full version, this would validate credentials
    if username == "admin" and password == "admin123":
        return {
            "access_token": "test-token-123",
            "token_type": "bearer",
            "user": {
                "id": "1",
                "username": "admin",
                "role": "admin",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }
    else:
        return {"error": "Invalid credentials", "status": "error"}

@app.get("/api/auth/test")
async def test_auth():
    return {"message": "Auth router is working", "status": "ok"}

# Dashboard endpoints
@app.get("/api/dashboard/stats")
async def dashboard_stats():
    """Get dashboard statistics"""
    return {
        "total_reservations": 0,
        "today_reservations": 0,
        "total_customers": 0,
        "weekly_reservations": [0, 0, 0, 0, 0, 0, 0],
        "monthly_revenue": 0
    }

@app.get("/api/dashboard/notes")
async def dashboard_notes():
    """Get dashboard notes"""
    return [
        {
            "id": "1",
            "content": "Welcome to The Castle Pub!",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    ]

@app.get("/api/dashboard/customers")
async def dashboard_customers():
    """Get customer list"""
    return [
        {
            "id": "1",
            "name": "Sample Customer",
            "email": "customer@example.com",
            "phone": "+1234567890",
            "total_reservations": 0,
            "last_visit": None
        }
    ]

@app.get("/api/dashboard/today")
async def today_reservations():
    """Get today's reservations"""
    return [
        {
            "id": "1",
            "customer_name": "Sample Reservation",
            "email": "reservation@example.com",
            "phone": "+1234567890",
            "date": date.today().isoformat(),
            "time": "19:00",
            "party_size": 4,
            "room_name": "Main Room",
            "status": "confirmed",
            "created_at": datetime.now().isoformat()
        }
    ]

@app.get("/api/rooms")
async def get_rooms():
    """Get rooms list"""
    return [
        {
            "id": "1",
            "name": "Main Room",
            "description": "Main dining area",
            "capacity": 50,
            "is_active": True
        },
        {
            "id": "2", 
            "name": "Biergarden",
            "description": "Outdoor seating area",
            "capacity": 30,
            "is_active": True
        }
    ]

@app.get("/api/settings/restaurant")
async def restaurant_settings():
    """Get restaurant settings"""
    return {
        "name": "The Castle Pub",
        "description": "A cozy pub with great food and atmosphere",
        "address": "123 Castle Street",
        "phone": "+1234567890",
        "email": "info@castlepub.com",
        "max_party_size": 20,
        "opening_hours": {
            "monday": {"open": "11:00", "close": "23:00", "is_open": True},
            "tuesday": {"open": "11:00", "close": "23:00", "is_open": True},
            "wednesday": {"open": "11:00", "close": "23:00", "is_open": True},
            "thursday": {"open": "11:00", "close": "23:00", "is_open": True},
            "friday": {"open": "11:00", "close": "00:00", "is_open": True},
            "saturday": {"open": "11:00", "close": "00:00", "is_open": True},
            "sunday": {"open": "12:00", "close": "22:00", "is_open": True}
        }
    } 