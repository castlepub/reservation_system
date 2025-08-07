#!/usr/bin/env python3
"""
Test script to verify database connection on Railway
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from sqlalchemy import text

def test_db_connection():
    """Test database connection"""
    try:
        print("Testing database connection...")
        
        # Test basic connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            
            # Test if tables exist
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            print(f"✅ Found {len(tables)} tables: {tables}")
            
            # Test if we can query reservations
            if 'reservations' in tables:
                result = connection.execute(text("SELECT COUNT(*) FROM reservations"))
                count = result.scalar()
                print(f"✅ Reservations table has {count} records")
            
            # Test if we can query rooms
            if 'rooms' in tables:
                result = connection.execute(text("SELECT COUNT(*) FROM rooms"))
                count = result.scalar()
                print(f"✅ Rooms table has {count} records")
                
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_db_connection()
    if success:
        print("\n🎉 Database connection test passed!")
    else:
        print("\n💥 Database connection test failed!")
        sys.exit(1) 