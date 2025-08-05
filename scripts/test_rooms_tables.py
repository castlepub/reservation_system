#!/usr/bin/env python3
"""
Test script to verify rooms and tables relationships in the database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.room import Room
from app.models.table import Table
from app.models.table_layout import TableLayout, RoomLayout


def test_rooms_tables():
    """Test the rooms and tables relationships"""
    db = SessionLocal()
    
    try:
        print("=== Testing Rooms and Tables Relationships ===\n")
        
        # Get all rooms
        rooms = db.query(Room).all()
        print(f"Found {len(rooms)} rooms:")
        for room in rooms:
            print(f"  - {room.name} (ID: {room.id}) - Active: {room.active}")
        
        print("\n" + "="*50 + "\n")
        
        # Get all tables
        tables = db.query(Table).all()
        print(f"Found {len(tables)} tables:")
        for table in tables:
            room = db.query(Room).filter(Room.id == table.room_id).first()
            room_name = room.name if room else "UNKNOWN ROOM"
            print(f"  - {table.name} (ID: {table.id}) - Room: {room_name} - Capacity: {table.capacity} - Active: {table.active}")
        
        print("\n" + "="*50 + "\n")
        
        # Test relationships
        print("Testing relationships:")
        for room in rooms:
            room_tables = db.query(Table).filter(Table.room_id == room.id).all()
            print(f"  {room.name}: {len(room_tables)} tables")
            for table in room_tables:
                print(f"    - {table.name} ({table.capacity} seats)")
        
        print("\n" + "="*50 + "\n")
        
        # Check for orphaned tables
        orphaned_tables = db.query(Table).outerjoin(Room).filter(Room.id.is_(None)).all()
        if orphaned_tables:
            print(f"WARNING: Found {len(orphaned_tables)} orphaned tables:")
            for table in orphaned_tables:
                print(f"  - {table.name} (ID: {table.id}) - Room ID: {table.room_id}")
        else:
            print("✓ No orphaned tables found")
        
        print("\n" + "="*50 + "\n")
        
        # Check table layouts
        table_layouts = db.query(TableLayout).all()
        print(f"Found {len(table_layouts)} table layouts:")
        for layout in table_layouts:
            table = db.query(Table).filter(Table.id == layout.table_id).first()
            room = db.query(Room).filter(Room.id == layout.room_id).first()
            table_name = table.name if table else "UNKNOWN TABLE"
            room_name = room.name if room else "UNKNOWN ROOM"
            print(f"  - Table: {table_name} - Room: {room_name} - Position: ({layout.x_position}, {layout.y_position})")
        
        print("\n" + "="*50 + "\n")
        
        # Check room layouts
        room_layouts = db.query(RoomLayout).all()
        print(f"Found {len(room_layouts)} room layouts:")
        for layout in room_layouts:
            room = db.query(Room).filter(Room.id == layout.room_id).first()
            room_name = room.name if room else "UNKNOWN ROOM"
            print(f"  - Room: {room_name} - Size: {layout.width}x{layout.height}")
        
        print("\n=== Test completed ===")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_rooms_tables() 