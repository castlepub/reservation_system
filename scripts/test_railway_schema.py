#!/usr/bin/env python3
"""
Script to test Railway database schema and check for specific columns.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor

# Railway PostgreSQL connection details
DB_CONFIG = {
    'host': 'nozomi.proxy.rlwy.net',
    'port': 42902,
    'database': 'railway',
    'user': 'postgres',
    'password': 'JcKlUqURohAAYSSHxfEtkPkfUaurqjSm'
}

def test_railway_schema():
    """Test Railway database schema"""
    print("=== Testing Railway Database Schema ===\n")
    
    try:
        # Connect to Railway database
        print("Connecting to Railway PostgreSQL database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("✓ Connected successfully!\n")
        
        # Check reservations table columns
        print("1. Checking reservations table columns...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'reservations'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        
        print(f"   Found {len(columns)} columns in reservations table:")
        for col in columns:
            print(f"     - {col['column_name']} ({col['data_type']}) - Nullable: {col['is_nullable']}")
        
        # Check if duration_hours exists
        duration_hours_exists = any(col['column_name'] == 'duration_hours' for col in columns)
        print(f"\n   duration_hours column exists: {'✓' if duration_hours_exists else '❌'}")
        
        # Check table_layouts table
        print("\n2. Checking table_layouts table...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'table_layouts'
        """)
        table_layouts_exists = cursor.fetchone()
        print(f"   table_layouts table exists: {'✓' if table_layouts_exists else '❌'}")
        
        # Check room_layouts table
        print("\n3. Checking room_layouts table...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'room_layouts'
        """)
        room_layouts_exists = cursor.fetchone()
        print(f"   room_layouts table exists: {'✓' if room_layouts_exists else '❌'}")
        
        # Test a simple query on reservations
        print("\n4. Testing reservations query...")
        cursor.execute("SELECT customer_name, duration_hours FROM reservations LIMIT 1")
        result = cursor.fetchone()
        if result:
            print(f"   ✓ Query successful - Found reservation: {result[0]} (Duration: {result[1]} hours)")
        else:
            print("   ⚠ No reservations found")

        print("\n5. Checking working_hours table...")
        try:
            cursor.execute("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'working_hours' ORDER BY ordinal_position")
            columns = cursor.fetchall()
            if columns:
                print(f"   working_hours table exists with {len(columns)} columns:")
                for col in columns:
                    print(f"     - {col[0]} ({col[1]}) - Nullable: {col[2]}")
                
                # Test working hours query
                cursor.execute("SELECT day_of_week, is_open FROM working_hours LIMIT 1")
                wh_result = cursor.fetchone()
                if wh_result:
                    print(f"   ✓ Working hours query successful - Found: {wh_result[0]} (Open: {wh_result[1]})")
                else:
                    print("   ⚠ No working hours entries found")
            else:
                print("   ❌ working_hours table does not exist")
        except Exception as e:
            print(f"   ❌ Error checking working_hours table: {e}")

        print("\n=== Schema Test completed ===")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error testing schema: {e}")
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    test_railway_schema() 