#!/usr/bin/env python3
"""
Test script to check daily view API response and identify issues
"""

import requests
import json
from datetime import datetime

# API base URL
API_BASE_URL = "https://reservationsystem-production-10cc.up.railway.app"

def test_daily_view():
    """Test the daily view endpoint"""
    try:
        # Test date
        test_date = datetime.now().strftime("%Y-%m-%d")
        
        # Call the daily view endpoint
        url = f"{API_BASE_URL}/api/layout/daily/{test_date}"
        print(f"Testing URL: {url}")
        
        response = requests.get(url)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response data structure:")
            print(f"- Date: {data.get('date')}")
            print(f"- Rooms count: {len(data.get('rooms', []))}")
            
            for i, room in enumerate(data.get('rooms', [])):
                print(f"\nRoom {i+1}: {room.get('name')}")
                print(f"- Tables count: {len(room.get('tables', []))}")
                print(f"- Reservations count: {len(room.get('reservations', []))}")
                
                # Check each table
                for j, table in enumerate(room.get('tables', [])):
                    print(f"  Table {j+1}: {table.get('table_name')}")
                    print(f"    - Has reservations property: {'reservations' in table}")
                    print(f"    - Reservations count: {len(table.get('reservations', []))}")
                    
                    # Check if reservations array exists and is valid
                    reservations = table.get('reservations', [])
                    if reservations is None:
                        print(f"    - ERROR: reservations is None!")
                    elif not isinstance(reservations, list):
                        print(f"    - ERROR: reservations is not a list: {type(reservations)}")
                    else:
                        print(f"    - Reservations array is valid")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Error testing daily view: {str(e)}")

def test_admin_tables():
    """Test the admin tables endpoint"""
    try:
        url = f"{API_BASE_URL}/admin/tables"
        print(f"\nTesting admin tables URL: {url}")
        
        response = requests.get(url)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Tables count: {len(data)}")
            
            for table in data[:3]:  # Show first 3 tables
                print(f"- Table: {table.get('name')} in {table.get('room_name')}")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Error testing admin tables: {str(e)}")

def test_admin_rooms():
    """Test the admin rooms endpoint"""
    try:
        url = f"{API_BASE_URL}/admin/rooms"
        print(f"\nTesting admin rooms URL: {url}")
        
        response = requests.get(url)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Rooms count: {len(data)}")
            
            for room in data:
                print(f"- Room: {room.get('name')}")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Error testing admin rooms: {str(e)}")

if __name__ == "__main__":
    print("Testing Daily View API Fix")
    print("=" * 50)
    
    test_daily_view()
    test_admin_tables()
    test_admin_rooms() 