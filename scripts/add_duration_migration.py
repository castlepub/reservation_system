#!/usr/bin/env python3
"""
Migration script to add duration_hours column to reservations table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import SessionLocal

def migrate_duration_column():
    """Add duration_hours column to reservations table"""
    db = SessionLocal()
    
    try:
        # Check if duration_hours column already exists
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='reservations' AND column_name='duration_hours'
        """)).fetchone()
        
        if not result:
            print("Adding duration_hours column to reservations table...")
            
            # Add the column with default value 2
            db.execute(text("ALTER TABLE reservations ADD COLUMN duration_hours INTEGER DEFAULT 2 NOT NULL"))
            db.commit()
            
            print("✅ duration_hours column added successfully")
        else:
            print("✅ duration_hours column already exists")
        
        # Update existing reservations to have duration_hours = 2 if they don't have it
        db.execute(text("UPDATE reservations SET duration_hours = 2 WHERE duration_hours IS NULL"))
        db.commit()
        
        print("✅ All existing reservations updated with default duration")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error during migration: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🔄 Starting duration migration...")
    migrate_duration_column()
    print("✅ Migration completed successfully!") 