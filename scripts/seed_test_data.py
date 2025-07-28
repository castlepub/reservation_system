#!/usr/bin/env python3
"""
Seed the database with test data for demonstration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.reservation import Reservation, ReservationStatus, ReservationType
from app.models.room import Room
from app.models.table import Table
from app.models.user import User, UserRole
from app.models.reservation import DashboardNote
from app.core.security import get_password_hash
from datetime import datetime, date, time, timedelta
import random

# Test customers data
TEST_CUSTOMERS = [
    {
        "name": "Emma Thompson",
        "email": "emma.thompson@email.com",
        "phone": "+49 30 12345671"
    },
    {
        "name": "James Wilson",
        "email": "james.wilson@email.com", 
        "phone": "+49 30 12345672"
    },
    {
        "name": "Sophie Mueller",
        "email": "sophie.mueller@email.com",
        "phone": "+49 30 12345673"
    },
    {
        "name": "Michael Brown",
        "email": "michael.brown@email.com",
        "phone": "+49 30 12345674"
    },
    {
        "name": "Anna Schmidt",
        "email": "anna.schmidt@email.com",
        "phone": "+49 30 12345675"
    },
    {
        "name": "David Johnson",
        "email": "david.johnson@email.com",
        "phone": "+49 30 12345676"
    },
    {
        "name": "Lisa Weber",
        "email": "lisa.weber@email.com",
        "phone": "+49 30 12345677"
    },
    {
        "name": "Robert Davis",
        "email": "robert.davis@email.com",
        "phone": "+49 30 12345678"
    },
    {
        "name": "Maria Garcia",
        "email": "maria.garcia@email.com",
        "phone": "+49 30 12345679"
    },
    {
        "name": "Thomas Klein",
        "email": "thomas.klein@email.com",
        "phone": "+49 30 12345680"
    }
]

# Test reservation types and notes
RESERVATION_TYPES = [
    ReservationType.DINING,
    ReservationType.BIRTHDAY,
    ReservationType.TEAM_EVENT,
    ReservationType.FUN,
    ReservationType.PARTY,
    ReservationType.SPECIAL_EVENT
]

CUSTOMER_NOTES = [
    "Celebrating our anniversary!",
    "Please prepare a birthday cake",
    "Team building dinner for 8 people",
    "Vegetarian options needed",
    "Window table preferred",
    "Birthday surprise for my daughter",
    "Business meeting - quiet table please",
    "Celebrating graduation",
    "First date - romantic setting",
    "Family reunion dinner"
]

ADMIN_NOTES = [
    "VIP customer - special attention",
    "Regular customer - knows preferences",
    "Large group - coordinate service",
    "Special dietary requirements noted",
    "Requested specific server",
    "Birthday celebration - coordinate with kitchen",
    "Corporate client",
    "Anniversary couple - romantic setup",
    "First-time visitors",
    "Repeat booking from last month"
]

def seed_test_data():
    """Seed the database with test data"""
    db = SessionLocal()
    
    try:
        print("🌱 Seeding test data...")
        
        # Get existing rooms
        rooms = db.query(Room).all()
        if not rooms:
            print("❌ No rooms found. Please create rooms first.")
            return
        
        # Create test reservations for the next 7 days
        today = date.today()
        
        # Create some past reservations for customer history
        for i in range(20):
            past_date = today - timedelta(days=random.randint(1, 30))
            customer = random.choice(TEST_CUSTOMERS)
            
            reservation = Reservation(
                customer_name=customer["name"],
                email=customer["email"],
                phone=customer["phone"],
                party_size=random.randint(2, 8),
                date=past_date,
                time=time(hour=random.randint(12, 21), minute=random.choice([0, 30])),
                room_id=random.choice(rooms).id,
                reservation_type=random.choice(RESERVATION_TYPES),
                status=ReservationStatus.CONFIRMED,
                notes=random.choice(CUSTOMER_NOTES) if random.random() > 0.3 else None,
                admin_notes=random.choice(ADMIN_NOTES) if random.random() > 0.5 else None
            )
            db.add(reservation)
        
        # Create future reservations for the next 7 days
        for day_offset in range(7):
            reservation_date = today + timedelta(days=day_offset)
            
            # Create 3-6 reservations per day
            daily_reservations = random.randint(3, 6)
            
            for _ in range(daily_reservations):
                customer = random.choice(TEST_CUSTOMERS)
                
                reservation = Reservation(
                    customer_name=customer["name"],
                    email=customer["email"],
                    phone=customer["phone"],
                    party_size=random.randint(2, 10),
                    date=reservation_date,
                    time=time(hour=random.randint(12, 21), minute=random.choice([0, 30])),
                    room_id=random.choice(rooms).id,
                    reservation_type=random.choice(RESERVATION_TYPES),
                    status=ReservationStatus.CONFIRMED,
                    notes=random.choice(CUSTOMER_NOTES) if random.random() > 0.4 else None,
                    admin_notes=random.choice(ADMIN_NOTES) if random.random() > 0.6 else None
                )
                db.add(reservation)
        
        # Create some dashboard notes
        dashboard_notes = [
            {
                "title": "Staff Meeting Tomorrow",
                "content": "Don't forget the staff meeting tomorrow at 10 AM. We'll discuss the new menu items and service procedures.",
                "priority": "high",
                "author": "admin"
            },
            {
                "title": "Special Event This Weekend",
                "content": "We have a large wedding party this Saturday. Make sure all staff are prepared and we have extra decorations ready.",
                "priority": "urgent",
                "author": "admin"
            },
            {
                "title": "Kitchen Equipment Maintenance",
                "content": "The oven will be serviced on Monday morning. Plan accordingly for food preparation.",
                "priority": "normal",
                "author": "admin"
            },
            {
                "title": "New Wine Delivery",
                "content": "Received the new wine shipment. Please update the wine list and train staff on the new selections.",
                "priority": "normal",
                "author": "admin"
            },
            {
                "title": "Customer Feedback",
                "content": "Received excellent feedback about our service last week. Keep up the great work!",
                "priority": "normal",
                "author": "admin"
            }
        ]
        
        for note_data in dashboard_notes:
            note = DashboardNote(
                title=note_data["title"],
                content=note_data["content"],
                priority=note_data["priority"],
                author=note_data["author"]
            )
            db.add(note)
        
        db.commit()
        print("✅ Test data seeded successfully!")
        print(f"   - Created historical reservations for customer analytics")
        print(f"   - Created reservations for the next 7 days")
        print(f"   - Added {len(dashboard_notes)} dashboard notes")
        
    except Exception as e:
        print(f"❌ Error seeding test data: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_test_data() 