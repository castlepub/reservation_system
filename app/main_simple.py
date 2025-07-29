from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

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