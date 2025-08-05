#!/usr/bin/env python3
"""
Test script to verify API endpoints for rooms and tables.
"""

import requests
import json
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:8000"

def test_api():
    """Test the API endpoints"""
    print("=== Testing API Endpoints ===\n")
    
    try:
        # Test 1: Get rooms (public endpoint)
        print("1. Testing GET /api/rooms (public)")
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
        
        # Test 2: Get admin rooms (requires auth)
        print("2. Testing GET /admin/rooms (admin)")
        response = requests.get(f"{API_BASE_URL}/admin/rooms")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            rooms = response.json()
            print(f"   Found {len(rooms)} rooms:")
            for room in rooms:
                print(f"     - {room['name']} (ID: {room['id']}) - Active: {room['active']}")
        else:
            print(f"   Error: {response.text}")
        
        print("\n" + "-"*50 + "\n")
        
        # Test 3: Get admin tables (requires auth)
        print("3. Testing GET /admin/tables (admin)")
        response = requests.get(f"{API_BASE_URL}/admin/tables")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            tables = response.json()
            print(f"   Found {len(tables)} tables:")
            for table in tables:
                print(f"     - {table['name']} (Room ID: {table['room_id']}) - Capacity: {table['capacity']}")
        else:
            print(f"   Error: {response.text}")
        
        print("\n" + "-"*50 + "\n")
        
        # Test 4: Get tables filtered by room
        if response.status_code == 200:
            tables = response.json()
            if tables:
                first_room_id = tables[0]['room_id']
                print(f"4. Testing GET /admin/tables?room_id={first_room_id}")
                response = requests.get(f"{API_BASE_URL}/admin/tables?room_id={first_room_id}")
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    room_tables = response.json()
                    print(f"   Found {len(room_tables)} tables in room {first_room_id}:")
                    for table in room_tables:
                        print(f"     - {table['name']} - Capacity: {table['capacity']}")
                else:
                    print(f"   Error: {response.text}")
        
        print("\n" + "-"*50 + "\n")
        
        # Test 5: Check if server is running
        print("5. Testing server health")
        try:
            response = requests.get(f"{API_BASE_URL}/docs")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✓ Server is running and accessible")
            else:
                print("   ⚠ Server responded but docs not found")
        except requests.exceptions.ConnectionError:
            print("   ✗ Server is not running or not accessible")
            print("   Please start the server with: uvicorn app.main:app --reload")
        
        print("\n=== API Test completed ===")
        
    except Exception as e:
        print(f"Error during API test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_api() 