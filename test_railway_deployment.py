#!/usr/bin/env python3
"""
Simple Railway Deployment Test
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_environment():
    """Test environment variables"""
    print("🔍 Testing Environment Variables...")
    
    # Check essential variables
    essential_vars = {
        'SECRET_KEY': os.getenv('SECRET_KEY'),
        'DATABASE_URL': os.getenv('DATABASE_URL'),
        'PORT': os.getenv('PORT', '8000')
    }
    
    for var, value in essential_vars.items():
        if value:
            if var == 'SECRET_KEY':
                print(f"✅ {var}: {'*' * len(value)}")
            elif var == 'DATABASE_URL':
                print(f"✅ {var}: {value[:50]}...")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
    
    # Check PostgreSQL specific variables
    pg_vars = {
        'PGHOST': os.getenv('PGHOST'),
        'PGUSER': os.getenv('PGUSER'),
        'PGPASSWORD': os.getenv('PGPASSWORD'),
        'PGDATABASE': os.getenv('PGDATABASE')
    }
    
    print("\n📊 PostgreSQL Variables:")
    for var, value in pg_vars.items():
        if value:
            if 'PASSWORD' in var:
                print(f"  ✅ {var}: {'*' * len(value)}")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: Not set")

def test_imports():
    """Test if all required modules can be imported"""
    print("\n📦 Testing Module Imports...")
    
    try:
        import fastapi
        print("✅ FastAPI imported successfully")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import uvicorn
        print("✅ Uvicorn imported successfully")
    except ImportError as e:
        print(f"❌ Uvicorn import failed: {e}")
        return False
    
    try:
        import sqlalchemy
        print("✅ SQLAlchemy imported successfully")
    except ImportError as e:
        print(f"❌ SQLAlchemy import failed: {e}")
        return False
    
    return True

def test_database_connection():
    """Test database connection"""
    print("\n🗄️ Testing Database Connection...")
    
    try:
        from app.core.database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"✅ Database connected! Test result: {row[0]}")
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        return False

def test_app_startup():
    """Test if the FastAPI app can start"""
    print("\n🚀 Testing App Startup...")
    
    try:
        from app.main import app
        print("✅ FastAPI app created successfully")
        
        # Test health endpoint
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        response = client.get("/health")
        print(f"✅ Health check response: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        return True
        
    except Exception as e:
        print(f"❌ App startup failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        return False

def main():
    """Main test function"""
    print("🏰 Railway Deployment Test")
    print("=" * 50)
    
    # Test environment
    test_environment()
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed. Check requirements.txt")
        sys.exit(1)
    
    # Test database
    if not test_database_connection():
        print("\n❌ Database connection failed.")
        print("   Make sure PostgreSQL service is added to Railway")
        sys.exit(1)
    
    # Test app
    if not test_app_startup():
        print("\n❌ App startup failed.")
        sys.exit(1)
    
    print("\n🎉 All tests passed! Your app should work on Railway.")

if __name__ == "__main__":
    main() 