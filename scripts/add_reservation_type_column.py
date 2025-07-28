#!/usr/bin/env python3
"""
Standalone script to add the missing reservation_type column to the reservations table.
This script can be run directly on production to fix the database schema issue.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def get_database_url():
    """Get database URL from environment variables"""
    return os.getenv('DATABASE_URL') or os.getenv('PGURI')

def add_reservation_type_column():
    """Add the reservation_type column to the reservations table"""
    database_url = get_database_url()
    
    if not database_url:
        print("Error: DATABASE_URL or PGURI environment variable not set")
        sys.exit(1)
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("Connected to database successfully")
        
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'reservations' 
            AND column_name = 'reservation_type'
        """)
        
        if cursor.fetchone():
            print("✓ reservation_type column already exists")
            return
        
        print("Adding reservation_type column...")
        
        # Create the enum type first
        cursor.execute("""
            DO $$ BEGIN
                CREATE TYPE reservationtype AS ENUM (
                    'dining', 'fun', 'team_event', 'birthday', 'party', 'special_event'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        
        # Add the column
        cursor.execute("""
            ALTER TABLE reservations 
            ADD COLUMN reservation_type reservationtype 
            DEFAULT 'dining' NOT NULL
        """)
        
        print("✓ Successfully added reservation_type column")
        print("✓ Set default value to 'dining' for all existing reservations")
        
        # Verify the column was added
        cursor.execute("""
            SELECT COUNT(*) as total_reservations,
                   COUNT(reservation_type) as reservations_with_type
            FROM reservations
        """)
        
        result = cursor.fetchone()
        if result:
            total, with_type = result
            print(f"✓ Verified: {with_type}/{total} reservations now have reservation_type set")
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Adding reservation_type column to reservations table...")
    print("=" * 60)
    add_reservation_type_column()
    print("=" * 60)
    print("Migration completed successfully!")
    print("The reservation system should now work without errors.")