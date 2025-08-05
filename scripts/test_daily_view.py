#!/usr/bin/env python3
"""
Test script to debug daily view database issues
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from datetime import datetime

def get_railway_db_connection():
    """Get connection to Railway PostgreSQL database"""
    # Railway database connection details
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/reservation_system')
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error connecting to Railway database: {e}")
        return None

def test_daily_view_data():
    """Test the daily view data retrieval"""
    conn = get_railway_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        print("Testing daily view data retrieval on Railway database...")
        
        # Test 1: Get rooms
        print("\n1. Testing rooms query...")
        cursor.execute("SELECT id, name, description FROM rooms WHERE active = true")
        rooms = cursor.fetchall()
        print(f"Found {len(rooms)} active rooms")
        for room in rooms:
            print(f"  - Room: {room[1]} (ID: {room[0]})")
        
        # Test 2: Get tables for first room
        if rooms:
            print(f"\n2. Testing tables query for room {rooms[0][1]}...")
            cursor.execute("SELECT id, name, capacity FROM tables WHERE room_id = %s AND active = true", (rooms[0][0],))
            tables = cursor.fetchall()
            print(f"Found {len(tables)} active tables")
            for table in tables:
                print(f"  - Table: {table[1]} (Capacity: {table[2]})")
        
        # Test 3: Get reservations for today
        print(f"\n3. Testing reservations query for today...")
        today = datetime.now().date()
        cursor.execute("SELECT id, customer_name, time, party_size, status FROM reservations WHERE date = %s", (today,))
        reservations = cursor.fetchall()
        print(f"Found {len(reservations)} reservations for today")
        for reservation in reservations:
            print(f"  - Reservation: {reservation[1]} at {reservation[2]}")
        
        # Test 4: Test the full daily view logic
        print(f"\n4. Testing full daily view logic...")
        daily_data = {
            "date": today.isoformat(),
            "rooms": []
        }
        
        for room in rooms:
            try:
                # Get tables for this room
                cursor.execute("SELECT id, name, capacity FROM tables WHERE room_id = %s AND active = true", (room[0],))
                tables = cursor.fetchall()
                
                # Get reservations for this date and room
                cursor.execute("SELECT id, customer_name, time, party_size, status, table_id FROM reservations WHERE date = %s AND room_id = %s", (today, room[0]))
                reservations = cursor.fetchall()
                
                print(f"  Room {room[1]}: {len(tables)} tables, {len(reservations)} reservations")
                
                # Convert tables to layout format
                table_layouts = []
                for i, table in enumerate(tables):
                    # Check if table has reservations
                    table_reservations = [r for r in reservations if r[5] == table[0]]  # r[5] is table_id
                    status = "reserved" if table_reservations else "available"
                    
                    table_layouts.append({
                        "layout_id": table[0],
                        "table_id": table[0],
                        "table_name": table[1],
                        "capacity": table[2],
                        "status": status
                    })
                
                daily_data["rooms"].append({
                    "id": room[0],
                    "name": room[1],
                    "tables": table_layouts,
                    "reservations": [
                        {
                            "id": r[0],
                            "customer_name": r[1],
                            "time": str(r[2]),
                            "party_size": r[3],
                            "status": r[4],
                            "table_id": r[5]
                        } for r in reservations
                    ]
                })
                
            except Exception as e:
                print(f"  Error processing room {room[0]}: {str(e)}")
                continue
        
        print(f"\n5. Final result: {len(daily_data['rooms'])} rooms processed successfully")
        return daily_data
        
    except Exception as e:
        print(f"Error in test: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    result = test_daily_view_data()
    if result:
        print("\n✅ Daily view test completed successfully!")
    else:
        print("\n❌ Daily view test failed!") 