#!/usr/bin/env python3
"""
Test script to verify the new public endpoints for rooms and tables.
"""

import requests
import json
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:8000"

def test_public_endpoints():
    """Test the public endpoints for rooms and tables"""
    print("=== Testing Public Endpoints ===\n")
    
    try:
        # Test 1: Get all rooms
        print("1. Testing GET /api/rooms")
        response = requests.get(f"{API_BASE_URL}/api/rooms")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            rooms = response.json()
            print(f"   Found {len(rooms)} rooms:")
            for room in rooms:
                print(f"     - {room['name']} (ID: {room['id']})")
        else:
            print(f"   Error: {response.text}")
        
        print("\n" + "-"*50 + "\n")
        
        # Test 2: Get all tables
        print("2. Testing GET /api/tables")
        response = requests.get(f"{API_BASE_URL}/api/tables")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            tables = response.json()
            print(f"   Found {len(tables)} tables:")
            for table in tables:
                print(f"     - {table['name']} (Room ID: {table['room_id']}) - Capacity: {table['capacity']}")
        else:
            print(f"   Error: {response.text}")
        
        print("\n" + "-"*50 + "\n")
        
        # Test 3: Get tables for a specific room
        if response.status_code == 200:
            tables = response.json()
            if tables:
                first_room_id = tables[0]['room_id']
                print(f"3. Testing GET /api/rooms/{first_room_id}/tables")
                response = requests.get(f"{API_BASE_URL}/api/rooms/{first_room_id}/tables")
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    room_tables = response.json()
                    print(f"   Found {len(room_tables)} tables in room {first_room_id}:")
                    for table in room_tables:
                        print(f"     - {table['name']} - Capacity: {table['capacity']}")
                else:
                    print(f"   Error: {response.text}")
        
        print("\n" + "-"*50 + "\n")
        
        # Test 4: Check room-table relationships
        print("4. Checking room-table relationships...")
        if response.status_code == 200:
            rooms_response = requests.get(f"{API_BASE_URL}/api/rooms")
            tables_response = requests.get(f"{API_BASE_URL}/api/tables")
            
            if rooms_response.status_code == 200 and tables_response.status_code == 200:
                rooms = rooms_response.json()
                tables = tables_response.json()
                
                # Create a map of room_id to room name
                room_map = {room['id']: room['name'] for room in rooms}
                
                # Group tables by room
                room_table_map = {}
                for table in tables:
                    room_id = table['room_id']
                    if room_id not in room_table_map:
                        room_table_map[room_id] = []
                    room_table_map[room_id].append(table)
                
                for room in rooms:
                    room_id = room['id']
                    room_tables = room_table_map.get(room_id, [])
                    print(f"   {room['name']}: {len(room_tables)} tables")
                    for table in room_tables:
                        print(f"     - {table['name']} ({table['capacity']} seats)")
        
        print("\n=== Public Endpoints Test completed ===")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_public_endpoints() 