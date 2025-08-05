#!/usr/bin/env python3
"""
Script to connect to Railway PostgreSQL database and check rooms/tables.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor
import json

# Railway PostgreSQL connection details
DB_CONFIG = {
    'host': 'nozomi.proxy.rlwy.net',
    'port': 42902,
    'database': 'railway',
    'user': 'postgres',
    'password': 'JcKlUqURohAAYSSHxfEtkPkfUaurqjSm'
}

def check_railway_database():
    """Check the Railway database for rooms and tables"""
    print("=== Checking Railway PostgreSQL Database ===\n")
    
    try:
        # Connect to Railway database
        print("Connecting to Railway PostgreSQL database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        print("✓ Connected successfully!\n")
        
        # Check if tables exist
        print("1. Checking database tables...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print(f"   Found {len(tables)} tables:")
        for table in tables:
            print(f"     - {table['table_name']}")
        
        print("\n" + "-"*50 + "\n")
        
        # Check rooms table
        if any(t['table_name'] == 'rooms' for t in tables):
            print("2. Checking rooms table...")
            cursor.execute("SELECT * FROM rooms ORDER BY name")
            rooms = cursor.fetchall()
            print(f"   Found {len(rooms)} rooms:")
            for room in rooms:
                print(f"     - {room['name']} (ID: {room['id']}) - Active: {room['active']}")
        else:
            print("   ❌ No rooms table found")
        
        print("\n" + "-"*50 + "\n")
        
        # Check tables table
        if any(t['table_name'] == 'tables' for t in tables):
            print("3. Checking tables table...")
            cursor.execute("SELECT * FROM tables ORDER BY name")
            db_tables = cursor.fetchall()
            print(f"   Found {len(db_tables)} tables:")
            for table in db_tables:
                print(f"     - {table['name']} (Room ID: {table['room_id']}) - Capacity: {table['capacity']}")
        else:
            print("   ❌ No tables table found")
        
        print("\n" + "-"*50 + "\n")
        
        # Check relationships
        if any(t['table_name'] == 'rooms' for t in tables) and any(t['table_name'] == 'tables' for t in tables):
            print("4. Checking room-table relationships...")
            cursor.execute("""
                SELECT r.name as room_name, r.id as room_id, 
                       COUNT(t.id) as table_count
                FROM rooms r
                LEFT JOIN tables t ON r.id = t.room_id
                GROUP BY r.id, r.name
                ORDER BY r.name
            """)
            relationships = cursor.fetchall()
            
            for rel in relationships:
                print(f"   {rel['room_name']}: {rel['table_count']} tables")
                
                # Get tables for this room
                cursor.execute("""
                    SELECT name, capacity, active 
                    FROM tables 
                    WHERE room_id = %s 
                    ORDER BY name
                """, (rel['room_id'],))
                room_tables = cursor.fetchall()
                
                for table in room_tables:
                    print(f"     - {table['name']} ({table['capacity']} seats) - Active: {table['active']}")
        
        print("\n" + "-"*50 + "\n")
        
        # Check for orphaned tables
        print("5. Checking for orphaned tables...")
        cursor.execute("""
            SELECT t.name, t.room_id
            FROM tables t
            LEFT JOIN rooms r ON t.room_id = r.id
            WHERE r.id IS NULL
        """)
        orphaned = cursor.fetchall()
        
        if orphaned:
            print(f"   ⚠ Found {len(orphaned)} orphaned tables:")
            for table in orphaned:
                print(f"     - {table['name']} (Room ID: {table['room_id']})")
        else:
            print("   ✓ No orphaned tables found")
        
        print("\n=== Railway Database Check completed ===")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error connecting to Railway database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_railway_database() 