#!/usr/bin/env python3
"""
Test script to verify the admin endpoints for tables and rooms.
"""

import requests
import json
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:8000"

def test_admin_endpoints():
    """Test the admin endpoints for tables and rooms"""
    print("=== Testing Admin Endpoints ===\n")
    
    # Test with auth headers
    headers = {
        "Authorization": "Bearer temporary_token_12345"
    }
    
    try:
        # Test 1: Get admin rooms
        print("1. Testing GET /admin/rooms (with auth)")
        response = requests.get(f"{API_BASE_URL}/admin/rooms", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            rooms = response.json()
            print(f"   Found {len(rooms)} rooms:")
            for room in rooms:
                print(f"     - {room['name']} (ID: {room['id']}) - Active: {room['active']}")
        else:
            print(f"   Error: {response.text}")
        
        print("\n" + "-"*50 + "\n")
        
        # Test 2: Get admin tables
        print("2. Testing GET /admin/tables (with auth)")
        response = requests.get(f"{API_BASE_URL}/admin/tables", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            tables = response.json()
            print(f"   Found {len(tables)} tables:")
            for table in tables:
                print(f"     - {table['name']} (Room: {table['room_name']}) - Capacity: {table['capacity']}")
        else:
            print(f"   Error: {response.text}")
        
        print("\n" + "-"*50 + "\n")
        
        # Test 3: Get admin reservations
        print("3. Testing GET /admin/reservations (with auth)")
        response = requests.get(f"{API_BASE_URL}/admin/reservations", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            reservations = response.json()
            print(f"   Found {len(reservations)} reservations:")
            for reservation in reservations:
                print(f"     - {reservation['customer_name']} ({reservation['date']} at {reservation['time']}) - {reservation['party_size']} people")
        else:
            print(f"   Error: {response.text}")
        
        print("\n=== Admin Endpoints Test completed ===")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_admin_endpoints() 