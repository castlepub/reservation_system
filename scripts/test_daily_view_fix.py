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
            
            # Check each room
            for i, room in enumerate(data.get('rooms', [])):
                print(f"\nRoom {i+1}: {room.get('name', 'Unknown')}")
                print(f"  - ID: {room.get('id')}")
                print(f"  - Tables count: {len(room.get('tables', []))}")
                print(f"  - Reservations count: {len(room.get('reservations', []))}")
                
                # Check tables
                for j, table in enumerate(room.get('tables', [])):
                    print(f"    Table {j+1}: {table.get('table_name', 'Unknown')}")
                    print(f"      - Capacity: {table.get('capacity', 0)}")
                    print(f"      - Position: ({table.get('x_position', 0)}, {table.get('y_position', 0)})")
                    print(f"      - Reservations: {len(table.get('reservations', []))}")
                
                # Check reservations
                for j, reservation in enumerate(room.get('reservations', [])):
                    print(f"    Reservation {j+1}: {reservation.get('customer_name', 'Unknown')}")
                    print(f"      - ID: {reservation.get('id')}")
                    print(f"      - Party size: {reservation.get('party_size', 0)}")
                    print(f"      - Time: {reservation.get('time', 'Unknown')}")
                    print(f"      - Tables: {len(reservation.get('tables', []))}")
            
            return True
        else:
            print(f"Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error testing daily view: {e}")
        return False

def test_frontend_data_structure():
    """Test if the data structure matches what the frontend expects"""
    try:
        test_date = datetime.now().strftime("%Y-%m-%d")
        url = f"{API_BASE_URL}/api/layout/daily/{test_date}"
        
        response = requests.get(url)
        if response.status_code != 200:
            print("❌ API not responding")
            return False
        
        data = response.json()
        
        # Check required structure
        if 'rooms' not in data:
            print("❌ Missing 'rooms' key in response")
            return False
        
        if not isinstance(data['rooms'], list):
            print("❌ 'rooms' is not an array")
            return False
        
        for room in data['rooms']:
            # Check room structure
            if 'id' not in room:
                print("❌ Room missing 'id'")
                return False
            
            if 'name' not in room:
                print("❌ Room missing 'name'")
                return False
            
            if 'reservations' not in room:
                print("❌ Room missing 'reservations'")
                return False
            
            if not isinstance(room['reservations'], list):
                print("❌ Room reservations is not an array")
                return False
            
            # Check each reservation
            for reservation in room['reservations']:
                if 'id' not in reservation:
                    print("❌ Reservation missing 'id'")
                    return False
                
                if 'customer_name' not in reservation:
                    print("❌ Reservation missing 'customer_name'")
                    return False
                
                if 'party_size' not in reservation:
                    print("❌ Reservation missing 'party_size'")
                    return False
                
                if 'time' not in reservation:
                    print("❌ Reservation missing 'time'")
                    return False
                
                if 'status' not in reservation:
                    print("❌ Reservation missing 'status'")
                    return False
        
        print("✅ Data structure validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error validating data structure: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Daily View Fix")
    print("=" * 50)
    
    # Test 1: Basic API response
    print("\n1. Testing basic API response...")
    if test_daily_view():
        print("✅ Daily view API is working")
    else:
        print("❌ Daily view API has issues")
    
    # Test 2: Data structure validation
    print("\n2. Testing data structure...")
    if test_frontend_data_structure():
        print("✅ Data structure is correct")
    else:
        print("❌ Data structure has issues")
    
    print("\n🎉 Testing complete!") 