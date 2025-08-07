#!/usr/bin/env python3
"""
Script to initialize the database with basic data
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.room import Room
from app.models.table import Table
from app.models.settings import Settings
from app.models.working_hours import WorkingHours
from sqlalchemy import text

def init_database():
    """Initialize database with basic data"""
    try:
        print("Initializing database with basic data...")
        
        db = SessionLocal()
        
        # Test connection first
        result = db.execute(text("SELECT 1"))
        print("✅ Database connection working!")
        
        # Check if we have any rooms
        rooms = db.query(Room).all()
        if not rooms:
            print("Creating default room...")
            default_room = Room(
                name="Main Dining Room",
                description="The main dining area",
                active=True
            )
            db.add(default_room)
            db.commit()
            db.refresh(default_room)
            print(f"✅ Created room: {default_room.name}")
            
            # Create some default tables
            print("Creating default tables...")
            tables = [
                Table(name="T1", capacity=4, room_id=default_room.id, active=True),
                Table(name="T2", capacity=6, room_id=default_room.id, active=True),
                Table(name="T3", capacity=4, room_id=default_room.id, active=True),
                Table(name="T4", capacity=8, room_id=default_room.id, active=True),
            ]
            for table in tables:
                db.add(table)
            db.commit()
            print(f"✅ Created {len(tables)} default tables")
        else:
            print(f"✅ Found {len(rooms)} existing rooms")
        
        # Check if we have settings
        settings = db.query(Settings).first()
        if not settings:
            print("Creating default settings...")
            default_settings = Settings(
                restaurant_name="The Castle Pub",
                max_party_size=20,
                min_reservation_hours=0,
                max_reservation_days=90
            )
            db.add(default_settings)
            db.commit()
            print("✅ Created default settings")
        else:
            print("✅ Settings already exist")
        
        # Check if we have working hours
        working_hours = db.query(WorkingHours).all()
        if not working_hours:
            print("Creating default working hours...")
            days = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY']
            for day in days:
                wh = WorkingHours(
                    day_of_week=day,
                    is_open=True,
                    open_time="11:00",
                    close_time="23:00"
                )
                db.add(wh)
            db.commit()
            print("✅ Created default working hours")
        else:
            print(f"✅ Found {len(working_hours)} working hours entries")
        
        db.close()
        print("🎉 Database initialization completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        if 'db' in locals():
            db.close()
        return False

if __name__ == "__main__":
    success = init_database()
    if success:
        print("\n✅ Database is ready to use!")
    else:
        print("\n💥 Database initialization failed!")
        sys.exit(1) 