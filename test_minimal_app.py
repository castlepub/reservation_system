#!/usr/bin/env python3
"""
Minimal test app to check if basic imports work
"""
import sys
import os

print("🔍 Testing minimal app startup...")

try:
    print("1. Testing basic imports...")
    from fastapi import FastAPI
    print("✅ FastAPI imported successfully")
    
    print("2. Testing database imports...")
    from app.core.database import engine, Base
    print("✅ Database imports successful")
    
    print("3. Testing auth imports...")
    from app.api import auth
    print("✅ Auth router imported successfully")
    
    print("4. Testing user model...")
    from app.models.user import User, UserRole
    print("✅ User model imported successfully")
    
    print("5. Testing security...")
    from app.core.security import get_password_hash
    print("✅ Security imports successful")
    
    print("6. Creating minimal app...")
    app = FastAPI()
    app.include_router(auth.router)
    print("✅ Minimal app created successfully")
    
    print("🎉 All imports successful! The issue might be in deployment.")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    print(f"Error type: {type(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 