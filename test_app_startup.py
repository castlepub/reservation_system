#!/usr/bin/env python3
"""
Test script to verify app startup locally
"""

import os
import sys
from datetime import datetime

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)

def test_imports():
    """Test if all imports work"""
    log("🔍 Testing imports...")
    
    try:
        import fastapi
        log("✅ FastAPI imported")
        
        import uvicorn
        log("✅ Uvicorn imported")
        
        import sqlalchemy
        log("✅ SQLAlchemy imported")
        
        from app.main import app
        log("✅ App imported successfully")
        
        return True
    except Exception as e:
        log(f"❌ Import failed: {e}")
        return False

def test_ping_endpoint():
    """Test if the ping endpoint works"""
    log("🔍 Testing ping endpoint...")
    
    try:
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/ping")
        
        if response.status_code == 200:
            log("✅ Ping endpoint works")
            return True
        else:
            log(f"❌ Ping endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        log(f"❌ Ping test failed: {e}")
        return False

def main():
    """Run all tests"""
    log("🧪 Starting app startup tests...")
    
    if not test_imports():
        log("❌ Import tests failed")
        sys.exit(1)
    
    if not test_ping_endpoint():
        log("❌ Ping endpoint test failed")
        sys.exit(1)
    
    log("✅ All tests passed! App should start successfully.")

if __name__ == "__main__":
    main() 