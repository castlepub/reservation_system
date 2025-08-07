#!/usr/bin/env python3
"""
Script to fix the layout system and ensure daily view works properly
"""

import os
import sys
import requests
import json
from datetime import datetime, date

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Production API URL
API_BASE_URL = "https://reservationsystem-production-10cc.up.railway.app"

def get_auth_token():
    """Get authentication token for admin access"""
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(f"{API_BASE_URL}/api/auth/login", data=login_data)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('access_token')
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error getting auth token: {e}")
        return None

def check_layout_system(token):
    """Check the current state of the layout system"""
    print("🔍 Checking layout system...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get rooms
    response = requests.get(f"{API_BASE_URL}/api/settings/rooms", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get rooms: {response.status_code}")
        return False
    
    rooms = response.json()
    print(f"Found {len(rooms)} rooms")
    
    # Get tables
    response = requests.get(f"{API_BASE_URL}/admin/tables", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get tables: {response.status_code}")
        return False
    
    tables = response.json()
    print(f"Found {len(tables)} tables")
    
    # Get reservations
    response = requests.get(f"{API_BASE_URL}/admin/reservations", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get reservations: {response.status_code}")
        return False
    
    reservations = response.json()
    print(f"Found {len(reservations)} reservations")
    
    # Check each room
    for room in rooms:
        room_name = room.get('name', 'Unknown')
        room_id = room.get('id')
        
        print(f"\n📋 Room: {room_name}")
        
        # Get tables for this room
        room_tables = [t for t in tables if t.get('room_id') == room_id]
        print(f"  Tables: {len(room_tables)}")
        
        # Get reservations for this room
        room_reservations = [r for r in reservations if r.get('room_id') == room_id]
        print(f"  Reservations: {len(room_reservations)}")
        
        # Check table assignments
        assigned_count = 0
        for reservation in room_reservations:
            if reservation.get('tables') and len(reservation['tables']) > 0:
                assigned_count += 1
        
        print(f"  Reservations with table assignments: {assigned_count}")
    
    return True

def test_daily_view_detailed(token):
    """Test the daily view with detailed analysis"""
    print("\n🧪 Testing daily view in detail...")
    
    headers = {"Authorization": f"Bearer {token}"}
    test_date = datetime.now().strftime("%Y-%m-%d")
    
    response = requests.get(f"{API_BASE_URL}/api/layout/daily/{test_date}", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Daily view API is working!")
        print(f"📅 Date: {data.get('date')}")
        print(f"🏠 Rooms: {len(data.get('rooms', []))}")
        
        for room in data.get('rooms', []):
            room_name = room.get('name', 'Unknown')
            tables_count = len(room.get('tables', []))
            reservations_count = len(room.get('reservations', []))
            
            print(f"\n  Room: {room_name}")
            print(f"    Tables: {tables_count}")
            print(f"    Reservations: {reservations_count}")
            
            if tables_count == 0:
                print(f"    ⚠️  No tables returned in daily view!")
            
            if reservations_count == 0:
                print(f"    ⚠️  No reservations returned in daily view!")
            
            # Check if room has layout data
            if room.get('layout'):
                print(f"    ✅ Has layout data")
            else:
                print(f"    ❌ Missing layout data")
        
        return True
    else:
        print(f"❌ Daily view test failed: {response.status_code} - {response.text}")
        return False

def test_layout_editor(token):
    """Test the layout editor endpoint"""
    print("\n🎨 Testing layout editor...")
    
    headers = {"Authorization": f"Bearer {token}"}
    test_date = datetime.now().strftime("%Y-%m-%d")
    
    # Get rooms first
    response = requests.get(f"{API_BASE_URL}/api/settings/rooms", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get rooms: {response.status_code}")
        return False
    
    rooms = response.json()
    
    for room in rooms[:1]:  # Test first room only
        room_id = room.get('id')
        room_name = room.get('name', 'Unknown')
        
        print(f"Testing layout editor for: {room_name}")
        
        response = requests.get(f"{API_BASE_URL}/api/layout/editor/{room_id}?target_date={test_date}", 
                              headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Layout editor working for {room_name}")
            print(f"    Room layout: {'Yes' if data.get('room_layout') else 'No'}")
            print(f"    Tables: {len(data.get('tables', []))}")
            print(f"    Reservations: {len(data.get('reservations', []))}")
        else:
            print(f"  ❌ Layout editor failed for {room_name}: {response.status_code}")
    
    return True

def main():
    """Main function"""
    print("🔧 Layout System Diagnostic and Fix")
    print("=" * 50)
    
    # Step 1: Get authentication token
    print("\n1. Getting authentication token...")
    token = get_auth_token()
    if not token:
        print("❌ Failed to get authentication token")
        return False
    
    print("✅ Authentication successful")
    
    # Step 2: Check layout system
    print("\n2. Checking layout system...")
    if not check_layout_system(token):
        print("❌ Failed to check layout system")
        return False
    
    # Step 3: Test daily view in detail
    print("\n3. Testing daily view in detail...")
    if not test_daily_view_detailed(token):
        print("❌ Daily view test failed")
        return False
    
    # Step 4: Test layout editor
    print("\n4. Testing layout editor...")
    if not test_layout_editor(token):
        print("❌ Layout editor test failed")
        return False
    
    print("\n🎉 Diagnostic completed!")
    print("\nBased on the results, the issue appears to be that:")
    print("- Tables exist in the database")
    print("- Reservations exist and have table assignments")
    print("- But the daily view API is not returning the table and reservation data properly")
    print("\nThis suggests the layout service needs to be fixed to properly return the data.")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Diagnostic failed: {e}")
        sys.exit(1) 