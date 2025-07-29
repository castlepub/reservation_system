#!/usr/bin/env python3
"""
Robust Railway startup script with comprehensive error handling
"""

import os
import sys
import time
import traceback
from datetime import datetime

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)

def check_environment():
    """Check required environment variables"""
    log("🔍 Checking environment variables...")
    
    required_vars = [
        'DATABASE_URL',
        'SECRET_KEY',
        'SENDGRID_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        log(f"❌ Missing environment variables: {missing_vars}")
        return False
    
    log("✅ Environment variables check passed")
    return True

def test_imports():
    """Test critical imports"""
    log("🔍 Testing imports...")
    
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import psycopg2
        log("✅ All critical imports successful")
        return True
    except ImportError as e:
        log(f"❌ Import error: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    log("🔍 Testing database connection...")
    
    try:
        from app.core.database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            log("✅ Database connection successful")
            return True
    except Exception as e:
        log(f"❌ Database connection failed: {e}")
        return False

def start_application():
    """Start the FastAPI application"""
    log("🚀 Starting FastAPI application...")
    
    try:
        import uvicorn
        from app.main import app
        
        log("✅ FastAPI app imported successfully")
        
        # Start the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=int(os.getenv("PORT", 8000)),
            log_level="info"
        )
    except Exception as e:
        log(f"❌ Failed to start application: {e}")
        log(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main startup function"""
    log("🎯 Starting Castle Pub Reservation System...")
    
    # Check environment
    if not check_environment():
        log("❌ Environment check failed")
        sys.exit(1)
    
    # Test imports
    if not test_imports():
        log("❌ Import test failed")
        sys.exit(1)
    
    # Test database connection
    if not test_database_connection():
        log("❌ Database connection test failed")
        sys.exit(1)
    
    # Start application
    log("✅ All checks passed, starting application...")
    start_application()

if __name__ == "__main__":
    main() 