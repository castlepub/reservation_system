from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    return {"message": "The Castle Pub Reservation System", "status": "running"}

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
async def login():
    return {"message": "Login endpoint reached", "status": "ok"}

@app.get("/api/auth/test")
async def test_auth():
    return {"message": "Auth router is working", "status": "ok"} 