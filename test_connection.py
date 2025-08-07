#!/usr/bin/env python3
"""
Test script to debug database connection
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_connection():
    print("=== Database Connection Debug ===")
    
    # Check environment variables
    print(f"1. DATABASE_URL from env: {os.getenv('DATABASE_URL', 'NOT SET')}")
    
    # Check config
    try:
        from app.core.config import settings
        print(f"2. DATABASE_URL from config: {settings.DATABASE_URL}")
    except Exception as e:
        print(f"2. Config error: {e}")
    
    # Check if SQLite file exists
    sqlite_file = "castle_reservations.db"
    if os.path.exists(sqlite_file):
        print(f"3. SQLite file exists: {sqlite_file}")
    else:
        print(f"3. SQLite file does not exist")
    
    # Try to create engine
    try:
        from app.core.database import engine
        print(f"4. Engine created successfully")
        print(f"   Engine URL: {engine.url}")
        
        # Try to connect
        with engine.connect() as conn:
            result = conn.execute("SELECT 1 as test")
            print(f"5. Connection successful: {result.fetchone()}")
            
    except Exception as e:
        print(f"4. Engine/Connection error: {e}")
        print(f"   Error type: {type(e).__name__}")

if __name__ == "__main__":
    test_connection() 