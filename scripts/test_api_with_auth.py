#!/usr/bin/env python3
"""
Test script to verify API endpoints with authentication.
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

def test_api_with_auth():
    """Test the API endpoints with authentication"""
    print("=== Testing API Endpoints with Authentication ===\n")
    
    # Get auth token
    auth_token = get_auth_token()
    if not auth_token:
        print("❌ Could not get authentication token")
        return
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        # Test 1: Get admin rooms (with auth)
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
        
        # Test 2: Get admin tables (with auth)
        print("2. Testing GET /admin/tables (with auth)")
        response = requests.get(f"{API_BASE_URL}/admin/tables", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            tables = response.json()
            print(f"   Found {len(tables)} tables:")
            for table in tables:
                print(f"     - {table['name']} (Room ID: {table['room_id']}) - Capacity: {table['capacity']}")
        else:
            print(f"   Error: {response.text}")
        
        print("\n" + "-"*50 + "\n")
        
        # Test 3: Get tables filtered by room (with auth)
        if response.status_code == 200:
            tables = response.json()
            if tables:
                first_room_id = tables[0]['room_id']
                print(f"3. Testing GET /admin/tables?room_id={first_room_id} (with auth)")
                response = requests.get(f"{API_BASE_URL}/admin/tables?room_id={first_room_id}", headers=headers)
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    room_tables = response.json()
                    print(f"   Found {len(room_tables)} tables in room {first_room_id}:")
                    for table in room_tables:
                        print(f"     - {table['name']} - Capacity: {table['capacity']}")
                else:
                    print(f"   Error: {response.text}")
        
        print("\n" + "-"*50 + "\n")
        
        # Test 4: Check if server is running
        print("4. Testing server health")
        try:
            response = requests.get(f"{API_BASE_URL}/docs")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✓ Server is running and accessible")
            else:
                print("   ⚠ Server responded but docs not found")
        except requests.exceptions.ConnectionError:
            print("   ✗ Server is not running or not accessible")
        
        print("\n=== API Test with Authentication completed ===")
        
    except Exception as e:
        print(f"Error during API test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_with_auth() 