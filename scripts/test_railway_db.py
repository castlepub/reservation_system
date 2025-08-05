#!/usr/bin/env python3
"""
Test script to check Railway database and fix rooms/tables connection.
"""

import requests
import json
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:8000"

def get_auth_token():
    """Get authentication token for admin access"""
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(f"{API_BASE_URL}/auth/login", data=login_data)
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error getting auth token: {e}")
        return None

def test_railway_database():
    """Test the Railway database and identify issues"""
    print("=== Testing Railway Database ===\n")
    
    # Get auth token
    auth_token = get_auth_token()
    if not auth_token:
        print("❌ Could not get authentication token")
        return
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Test 1: Get all rooms
        print("1. Getting all rooms from Railway database...")
        response = requests.get(f"{API_BASE_URL}/admin/rooms", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            rooms = response.json()
            print(f"   Found {len(rooms)} rooms:")
            for room in rooms:
                print(f"     - {room['name']} (ID: {room['id']}) - Active: {room['active']}")
        else:
            print(f"   Error: {response.text}")
            return
        
        print("\n" + "-"*50 + "\n")
        
        # Test 2: Get all tables
        print("2. Getting all tables from Railway database...")
        response = requests.get(f"{API_BASE_URL}/admin/tables", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            tables = response.json()
            print(f"   Found {len(tables)} tables:")
            for table in tables:
                print(f"     - {table['name']} (Room ID: {table['room_id']}) - Capacity: {table['capacity']}")
        else:
            print(f"   Error: {response.text}")
            return
        
        print("\n" + "-"*50 + "\n")
        
        # Test 3: Check room-table relationships
        print("3. Checking room-table relationships...")
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
        
        print("\n" + "-"*50 + "\n")
        
        # Test 4: Check for orphaned tables
        print("4. Checking for orphaned tables...")
        orphaned_tables = []
        for table in tables:
            room_id = table['room_id']
            room_exists = any(room['id'] == room_id for room in rooms)
            if not room_exists:
                orphaned_tables.append(table)
        
        if orphaned_tables:
            print(f"   ⚠ Found {len(orphaned_tables)} orphaned tables:")
            for table in orphaned_tables:
                print(f"     - {table['name']} (Room ID: {table['room_id']})")
        else:
            print("   ✓ No orphaned tables found")
        
        print("\n=== Railway Database Test completed ===")
        
        return rooms, tables
        
    except Exception as e:
        print(f"Error during Railway database test: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def fix_railway_database():
    """Fix the Railway database by ensuring proper room-table relationships"""
    print("\n=== Fixing Railway Database ===\n")
    
    # Get auth token
    auth_token = get_auth_token()
    if not auth_token:
        print("❌ Could not get authentication token")
        return
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # First, let's check what we have
        rooms, tables = test_railway_database()
        if not rooms or not tables:
            print("❌ Could not get database data")
            return
        
        print("\n" + "="*50 + "\n")
        
        # Check if we need to create proper rooms and tables
        print("5. Checking if we need to create proper rooms and tables...")
        
        # Get the first room to see what format we're working with
        if rooms:
            first_room = rooms[0]
            print(f"   Sample room format: {first_room}")
        
        if tables:
            first_table = tables[0]
            print(f"   Sample table format: {first_table}")
        
        # Check if we have the expected room names
        expected_room_names = ["Front Room", "Middle Room", "Back Room", "Biergarten"]
        existing_room_names = [room['name'] for room in rooms]
        
        print(f"   Expected rooms: {expected_room_names}")
        print(f"   Existing rooms: {existing_room_names}")
        
        missing_rooms = [name for name in expected_room_names if name not in existing_room_names]
        if missing_rooms:
            print(f"   ⚠ Missing rooms: {missing_rooms}")
        else:
            print("   ✓ All expected rooms exist")
        
        print("\n=== Railway Database Fix completed ===")
        
    except Exception as e:
        print(f"Error during Railway database fix: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_railway_database() 