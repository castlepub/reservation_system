#!/usr/bin/env python3
"""
Database initialization script for The Castle Pub Reservation System.
This script creates sample rooms, tables, and an admin user.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.room import Room
from app.models.table import Table
import uuid


def init_db():
    """Initialize the database with sample data"""
    db = SessionLocal()
    
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        print("Creating admin user...")
        # Create admin user
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                password_hash=get_password_hash("admin123"),  # Change this in production!
                role=UserRole.ADMIN
            )
            db.add(admin_user)
            print("✓ Admin user created (username: admin, password: admin123)")
        else:
            print("✓ Admin user already exists")
        
        print("\nCreating rooms...")
        # Create sample rooms
        rooms_data = [
            {
                "name": "Front Room",
                "description": "Welcoming entrance area with street-side windows"
            },
            {
                "name": "Middle Room", 
                "description": "Central dining area with traditional pub atmosphere"
            },
            {
                "name": "Back Room",
                "description": "Quieter seating area perfect for intimate conversations"
            },
            {
                "name": "Biergarten",
                "description": "Outdoor seating area with authentic German beer garden experience"
            }
        ]
        
        created_rooms = {}
        for room_data in rooms_data:
            room = db.query(Room).filter(Room.name == room_data["name"]).first()
            if not room:
                room = Room(**room_data)
                db.add(room)
                db.flush()  # Get the ID
                print(f"✓ Created room: {room.name}")
            else:
                print(f"✓ Room already exists: {room.name}")
            created_rooms[room.name] = room
        
        print("\nCreating tables...")
        # Create sample tables for each room
        tables_data = {
            "Front Room": [
                {"name": "F1", "capacity": 4, "combinable": True, "x": 10, "y": 10, "width": 80, "height": 60},
                {"name": "F2", "capacity": 4, "combinable": True, "x": 100, "y": 10, "width": 80, "height": 60},
                {"name": "F3", "capacity": 2, "combinable": True, "x": 190, "y": 10, "width": 60, "height": 50},
                {"name": "F4", "capacity": 6, "combinable": True, "x": 10, "y": 80, "width": 100, "height": 70},
            ],
            "Middle Room": [
                {"name": "M1", "capacity": 4, "combinable": True, "x": 10, "y": 10, "width": 80, "height": 60},
                {"name": "M2", "capacity": 4, "combinable": True, "x": 100, "y": 10, "width": 80, "height": 60},
                {"name": "M3", "capacity": 6, "combinable": True, "x": 190, "y": 10, "width": 100, "height": 70},
                {"name": "M4", "capacity": 8, "combinable": True, "x": 10, "y": 80, "width": 120, "height": 80},
                {"name": "M5", "capacity": 2, "combinable": True, "x": 140, "y": 80, "width": 60, "height": 50},
                {"name": "M6", "capacity": 2, "combinable": True, "x": 210, "y": 80, "width": 60, "height": 50},
            ],
            "Back Room": [
                {"name": "B1", "capacity": 4, "combinable": True, "x": 10, "y": 10, "width": 80, "height": 60},
                {"name": "B2", "capacity": 6, "combinable": True, "x": 100, "y": 10, "width": 100, "height": 70},
                {"name": "B3", "capacity": 8, "combinable": True, "x": 10, "y": 80, "width": 120, "height": 80},
                {"name": "B4", "capacity": 10, "combinable": False, "x": 140, "y": 10, "width": 150, "height": 120},
            ],
            "Biergarten": [
                {"name": "BG1", "capacity": 6, "combinable": True, "x": 10, "y": 10, "width": 100, "height": 70},
                {"name": "BG2", "capacity": 6, "combinable": True, "x": 120, "y": 10, "width": 100, "height": 70},
                {"name": "BG3", "capacity": 8, "combinable": True, "x": 230, "y": 10, "width": 120, "height": 80},
                {"name": "BG4", "capacity": 8, "combinable": True, "x": 10, "y": 90, "width": 120, "height": 80},
                {"name": "BG5", "capacity": 10, "combinable": True, "x": 140, "y": 90, "width": 150, "height": 90},
                {"name": "BG6", "capacity": 12, "combinable": False, "x": 300, "y": 90, "width": 180, "height": 100},
            ]
        }
        
        for room_name, tables in tables_data.items():
            room = created_rooms.get(room_name)
            if room:
                for table_data in tables:
                    existing_table = db.query(Table).filter(
                        Table.room_id == room.id,
                        Table.name == table_data["name"]
                    ).first()
                    
                    if not existing_table:
                        table = Table(
                            room_id=room.id,
                            **table_data
                        )
                        db.add(table)
                        print(f"✓ Created table {table.name} ({table.capacity} seats) in {room_name}")
                    else:
                        print(f"✓ Table {table_data['name']} already exists in {room_name}")
        
        db.commit()
        print("\n✓ Database initialization completed successfully!")
        print("\nYou can now:")
        print("1. Start the application: uvicorn app.main:app --reload")
        print("2. Access the admin interface at: http://localhost:8000/docs")
        print("3. Login with: admin / admin123")
        print("4. Test the public API at: http://localhost:8000/docs#public")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db() 