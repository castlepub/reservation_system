# ULTRA MINIMAL FASTAPI APP FOR RAILWAY HEALTH CHECK
from datetime import datetime
from fastapi import FastAPI

# Create minimal FastAPI app
app = FastAPI(title="The Castle Pub Reservation System")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "The Castle Pub Reservation System", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong", "timestamp": datetime.utcnow().isoformat()}

# All other endpoints temporarily disabled for health check debugging