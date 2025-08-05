#!/usr/bin/env python3
"""
Script to test what database URL the application is using.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.database import engine

def test_database_connection():
    """Test what database the application is connecting to"""
    print("=== Testing Database Connection ===\n")
    
    print(f"1. DATABASE_URL from settings: {settings.DATABASE_URL}")
    print(f"2. DATABASE_URL from environment: {os.getenv('DATABASE_URL')}")
    print(f"3. Engine URL: {engine.url}")
    
    # Test the connection
    try:
        with engine.connect() as conn:
            print("4. ✓ Database connection successful!")
            
            # Check what database we're connected to
            if "sqlite" in str(engine.url):
                print("   Connected to: SQLite database")
            elif "postgresql" in str(engine.url):
                print("   Connected to: PostgreSQL database")
                # Get database name
                result = conn.execute("SELECT current_database()")
                db_name = result.fetchone()[0]
                print(f"   Database name: {db_name}")
            else:
                print("   Connected to: Unknown database type")
                
    except Exception as e:
        print(f"4. ❌ Database connection failed: {e}")
    
    print("\n=== Database Connection Test completed ===")

if __name__ == "__main__":
    test_database_connection() 