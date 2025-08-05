#!/usr/bin/env python3
"""
Script to test working hours validation functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date, time, datetime

# Railway PostgreSQL connection details
DB_CONFIG = {
    'host': 'nozomi.proxy.rlwy.net',
    'port': 42902,
    'database': 'railway',
    'user': 'postgres',
    'password': 'JcKlUqURohAAYSSHxfEtkPkfUaurqjSm'
}

def test_working_hours_validation():
    """Test working hours validation"""
    print("=== Testing Working Hours Validation ===\n")
    
    try:
        # Connect to Railway database
        print("Connecting to Railway PostgreSQL database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("✓ Connected successfully!\n")
        
        # Test 1: Check current working hours
        print("1. Checking current working hours...")
        cursor.execute("""
            SELECT day_of_week, is_open, open_time, close_time
            FROM working_hours
            ORDER BY day_of_week
        """)
        working_hours = cursor.fetchall()
        
        print(f"   Found {len(working_hours)} working hours entries:")
        for wh in working_hours:
            status = "OPEN" if wh['is_open'] else "CLOSED"
            times = f"{wh['open_time']} - {wh['close_time']}" if wh['open_time'] and wh['close_time'] else "No times set"
            print(f"     - {wh['day_of_week']}: {status} ({times})")
        
        # Test 2: Test validation for today
        today = date.today()
        print(f"\n2. Testing validation for today ({today}):")
        
        # Get today's working hours
        day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        today_day = day_names[today.weekday()].upper()
        
        cursor.execute("""
            SELECT is_open, open_time, close_time
            FROM working_hours
            WHERE day_of_week = %s
        """, (today_day,))
        
        today_hours = cursor.fetchone()
        
        if today_hours:
            print(f"   Today ({today_day}): {'OPEN' if today_hours['is_open'] else 'CLOSED'}")
            if today_hours['is_open'] and today_hours['open_time'] and today_hours['close_time']:
                print(f"   Hours: {today_hours['open_time']} - {today_hours['close_time']}")
                
                # Test some times
                test_times = [
                    time(12, 0),  # Noon
                    time(18, 0),  # 6 PM
                    time(23, 0),  # 11 PM
                    time(10, 0),  # 10 AM (before opening)
                ]
                
                print("\n   Testing reservation times:")
                for test_time in test_times:
                    is_valid = (
                        today_hours['is_open'] and
                        today_hours['open_time'] <= test_time <= today_hours['close_time']
                    )
                    status = "✓ VALID" if is_valid else "❌ INVALID"
                    print(f"     {test_time}: {status}")
            else:
                print("   No specific hours set")
        else:
            print(f"   No working hours found for {today_day}")
        
        # Test 3: Check if reservations table has duration_hours column
        print(f"\n3. Checking reservations table structure:")
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'reservations'
            AND column_name IN ('duration_hours', 'time', 'date')
            ORDER BY column_name
        """)
        columns = cursor.fetchall()
        
        for col in columns:
            print(f"   - {col['column_name']}: {col['data_type']}")
        
        cursor.close()
        conn.close()
        
        print("\n=== Working Hours Validation Test completed ===")
        
    except Exception as e:
        print(f"❌ Error testing working hours validation: {e}")

if __name__ == "__main__":
    test_working_hours_validation() 