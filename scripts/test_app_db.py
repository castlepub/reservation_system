#!/usr/bin/env python3
"""
Script to test the database through the application's database session.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.room import Room
from app.models.table import Table

def test_app_database():
    """Test the database through the application's session"""
    print("=== Testing Application Database Session ===\n")
    
    db = SessionLocal()
    
    try:
        # Test rooms
        print("1. Testing rooms through app session...")
        rooms = db.query(Room).all()
        print(f"   Found {len(rooms)} rooms:")
        for room in rooms:
            print(f"     - {room.name} (ID: {room.id}) - Active: {room.active}")
        
        print("\n" + "-"*50 + "\n")
        
        # Test tables
        print("2. Testing tables through app session...")
        tables = db.query(Table).all()
        print(f"   Found {len(tables)} tables:")
        for table in tables:
            room = db.query(Room).filter(Room.id == table.room_id).first()
            room_name = room.name if room else "UNKNOWN ROOM"
            print(f"     - {table.name} (Room: {room_name}) - Capacity: {table.capacity}")
        
        print("\n" + "-"*50 + "\n")
        
        # Test relationships
        print("3. Testing relationships through app session...")
        for room in rooms:
            room_tables = db.query(Table).filter(Table.room_id == room.id).all()
            print(f"   {room.name}: {len(room_tables)} tables")
            for table in room_tables:
                print(f"     - {table.name} ({table.capacity} seats)")
        
        print("\n=== Application Database Test completed ===")
        
    except Exception as e:
        print(f"❌ Error testing application database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_app_database() 