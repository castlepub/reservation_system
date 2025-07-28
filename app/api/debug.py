from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.reservation import Reservation
from app.api.deps import get_current_user
import logging

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/test")
def test_endpoint():
    """Simple test endpoint to check if API is working"""
    return {
        "status": "ok",
        "message": "API is working correctly",
        "timestamp": "2024-01-01T00:00:00Z"
    }


@router.get("/database")
def test_database(db: Session = Depends(get_db)):
    """Test database connection and basic queries"""
    try:
        # Test basic query
        reservation_count = db.query(Reservation).count()
        
        return {
            "status": "ok",
            "database": "connected",
            "reservation_count": reservation_count,
            "message": "Database is working"
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "error",
            "error": str(e),
            "message": "Database connection failed"
        }


@router.get("/auth-test")
def test_auth(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test authentication"""
    try:
        return {
            "status": "ok",
            "user": {
                "username": current_user.username,
                "role": current_user.role.value
            },
            "message": "Authentication working"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Authentication failed"
        }


@router.post("/trigger-migration")
def trigger_migration(db: Session = Depends(get_db)):
    """Trigger database migration without authentication for debugging"""
    try:
        from app.core.database import Base, engine
        from app.models.reservation import Reservation, ReservationStatus, ReservationType, DashboardNote
        from app.models.settings import WorkingHours, DayOfWeek, RestaurantSettings
        from app.models.room import Room
        from sqlalchemy import text
        from datetime import date, time, timedelta
        import random
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Add missing columns if they don't exist
        try:
            db.execute(text("SELECT reservation_type FROM reservations LIMIT 1"))
        except Exception:
            db.execute(text("ALTER TABLE reservations ADD COLUMN reservation_type VARCHAR DEFAULT 'dining'"))
            db.commit()
        
        try:
            db.execute(text("SELECT admin_notes FROM reservations LIMIT 1"))
        except Exception:
            db.execute(text("ALTER TABLE reservations ADD COLUMN admin_notes TEXT"))
            db.commit()
        
        # Update existing reservations
        try:
            db.execute(text("UPDATE reservations SET reservation_type = 'dining' WHERE reservation_type IS NULL"))
            db.commit()
        except Exception:
            pass
        
        # Check if we need test data
        reservation_count = db.query(Reservation).count()
        if reservation_count == 0:
            # Create test data
            rooms = db.query(Room).all()
            if rooms:
                test_customers = [
                    {"name": "Emma Thompson", "email": "emma.thompson@email.com", "phone": "+49 30 12345671"},
                    {"name": "James Wilson", "email": "james.wilson@email.com", "phone": "+49 30 12345672"},
                    {"name": "Sophie Mueller", "email": "sophie.mueller@email.com", "phone": "+49 30 12345673"}
                ]
                
                today = date.today()
                
                # Create a few test reservations
                for i in range(5):
                    customer = random.choice(test_customers)
                    reservation = Reservation(
                        customer_name=customer["name"],
                        email=customer["email"],
                        phone=customer["phone"],
                        party_size=random.randint(2, 6),
                        date=today + timedelta(days=random.randint(0, 3)),
                        time=time(hour=random.randint(12, 20), minute=random.choice([0, 30])),
                        room_id=random.choice(rooms).id,
                        reservation_type=ReservationType.DINING,
                        status=ReservationStatus.CONFIRMED,
                        notes="Test reservation"
                    )
                    db.add(reservation)
        
        # Create dashboard note if none exist
        note_count = db.query(DashboardNote).count()
        if note_count == 0:
            note = DashboardNote(
                title="System Ready",
                content="Your restaurant management system is now working correctly!",
                priority="normal",
                author="system"
            )
            db.add(note)
        
        db.commit()
        
        return {
            "status": "success",
            "message": "Database migration completed",
            "reservation_count": db.query(Reservation).count(),
            "note_count": db.query(DashboardNote).count()
        }
        
    except Exception as e:
        db.rollback()
        logging.error(f"Migration error: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Migration failed"
        } 