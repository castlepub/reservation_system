#!/usr/bin/env python3
"""
Deployment script to fix the layout system and daily view
- Sets up tables for each room
- Assigns existing reservations to tables
- Tests the daily view functionality
"""

import os
import sys
import requests
import json
from datetime import datetime, date
import time

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Production API URL
API_BASE_URL = "https://reservationsystem-production-10cc.up.railway.app"

def get_auth_token():
    """Get authentication token for admin access"""
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"  # Default admin password
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

def setup_rooms_with_tables(token):
    """Set up rooms with default tables"""
    print("🏗️  Setting up rooms with tables...")
    
    # Get existing rooms
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE_URL}/api/settings/rooms", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to get rooms: {response.status_code}")
        return False
    
    rooms = response.json()
    print(f"Found {len(rooms)} rooms")
    
    for room in rooms:
        room_name = room.get('name', 'Unknown')
        room_id = room.get('id')
        
        print(f"\n📋 Processing room: {room_name}")
        
        # Get existing tables for this room
        response = requests.get(f"{API_BASE_URL}/admin/tables", headers=headers)
        if response.status_code == 200:
            all_tables = response.json()
            room_tables = [t for t in all_tables if t.get('room_id') == room_id]
            
            if not room_tables:
                print(f"  ⚠️  No tables found for {room_name}, creating default tables...")
                
                # Create default tables based on room name
                table_configs = get_default_table_config(room_name)
                
                for config in table_configs:
                    table_data = {
                        "room_id": room_id,
                        "name": config['name'],
                        "capacity": config['capacity'],
                        "combinable": config['combinable']
                    }
                    
                    response = requests.post(f"{API_BASE_URL}/admin/tables", 
                                           json=table_data, headers=headers)
                    
                    if response.status_code == 200:
                        print(f"  ✅ Created table {config['name']} (capacity: {config['capacity']})")
                    else:
                        print(f"  ❌ Failed to create table {config['name']}: {response.status_code}")
            else:
                print(f"  ✅ {len(room_tables)} tables already exist for {room_name}")
        else:
            print(f"  ❌ Failed to get tables: {response.status_code}")
    
    return True

def get_default_table_config(room_name):
    """Get default table configuration based on room name"""
    room_name_lower = room_name.lower()
    
    if 'front' in room_name_lower:
        # Front room - smaller tables
        return [
            {"name": "F1", "capacity": 2, "combinable": True},
            {"name": "F2", "capacity": 2, "combinable": True},
            {"name": "F3", "capacity": 4, "combinable": True},
            {"name": "F4", "capacity": 4, "combinable": True},
            {"name": "F5", "capacity": 6, "combinable": True},
        ]
    elif 'back' in room_name_lower:
        # Back room - larger tables
        return [
            {"name": "B1", "capacity": 4, "combinable": True},
            {"name": "B2", "capacity": 4, "combinable": True},
            {"name": "B3", "capacity": 6, "combinable": True},
            {"name": "B4", "capacity": 6, "combinable": True},
            {"name": "B5", "capacity": 8, "combinable": True},
        ]
    elif 'outdoor' in room_name_lower:
        # Outdoor area - mixed sizes
        return [
            {"name": "O1", "capacity": 2, "combinable": True},
            {"name": "O2", "capacity": 2, "combinable": True},
            {"name": "O3", "capacity": 4, "combinable": True},
            {"name": "O4", "capacity": 4, "combinable": True},
            {"name": "O5", "capacity": 6, "combinable": True},
        ]
    else:
        # Default configuration for other rooms
        return [
            {"name": "T1", "capacity": 2, "combinable": True},
            {"name": "T2", "capacity": 2, "combinable": True},
            {"name": "T3", "capacity": 4, "combinable": True},
            {"name": "T4", "capacity": 4, "combinable": True},
            {"name": "T5", "capacity": 6, "combinable": True},
        ]

def assign_reservations_to_tables(token):
    """Assign existing reservations to tables"""
    print("\n📅 Assigning reservations to tables...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get all reservations
    response = requests.get(f"{API_BASE_URL}/admin/reservations", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to get reservations: {response.status_code}")
        return False
    
    reservations = response.json()
    print(f"Found {len(reservations)} reservations")
    
    assigned_count = 0
    for reservation in reservations:
        reservation_id = reservation.get('id')
        room_id = reservation.get('room_id')
        party_size = reservation.get('party_size', 0)
        status = reservation.get('status', 'confirmed')
        
        if status != 'confirmed':
            continue
        
        # Check if reservation already has table assignments
        if reservation.get('tables') and len(reservation['tables']) > 0:
            print(f"  ✅ Reservation {reservation_id} already has table assignments")
            continue
        
        # Get tables for this room
        response = requests.get(f"{API_BASE_URL}/admin/tables", headers=headers)
        if response.status_code != 200:
            continue
        
        all_tables = response.json()
        room_tables = [t for t in all_tables if t.get('room_id') == room_id]
        
        if not room_tables:
            continue
        
        # Find suitable table(s)
        suitable_tables = find_suitable_tables(room_tables, party_size)
        
        if suitable_tables:
            # Assign tables to reservation
            table_ids = [t['id'] for t in suitable_tables]
            
            response = requests.put(f"{API_BASE_URL}/admin/reservations/{reservation_id}/tables",
                                  json={"table_ids": table_ids}, headers=headers)
            
            if response.status_code == 200:
                assigned_count += 1
                print(f"  ✅ Assigned reservation {reservation_id} ({party_size} guests) to {len(suitable_tables)} table(s)")
            else:
                print(f"  ❌ Failed to assign tables to reservation {reservation_id}: {response.status_code}")
        else:
            print(f"  ⚠️  No suitable tables found for reservation {reservation_id} ({party_size} guests)")
    
    print(f"📊 Assigned {assigned_count} reservations to tables")
    return True

def find_suitable_tables(tables, party_size):
    """Find suitable tables for a party size"""
    # First, try to find a single table that can accommodate the party
    for table in tables:
        if table.get('capacity', 0) >= party_size:
            return [table]
    
    # If no single table works, try to combine tables
    if party_size <= 8:  # Only combine for reasonable party sizes
        for i, table1 in enumerate(tables):
            for table2 in tables[i+1:]:
                if table1.get('combinable') and table2.get('combinable'):
                    combined_capacity = table1.get('capacity', 0) + table2.get('capacity', 0)
                    if combined_capacity >= party_size:
                        return [table1, table2]
    
    return []

def test_daily_view(token):
    """Test the daily view functionality"""
    print("\n🧪 Testing daily view...")
    
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
            print(f"  - {room_name}: {tables_count} tables, {reservations_count} reservations")
        
        return True
    else:
        print(f"❌ Daily view test failed: {response.status_code} - {response.text}")
        return False

def main():
    """Main deployment function"""
    print("🚀 Layout System Deployment")
    print("=" * 50)
    
    # Step 1: Get authentication token
    print("\n1. Getting authentication token...")
    token = get_auth_token()
    if not token:
        print("❌ Failed to get authentication token")
        return False
    
    print("✅ Authentication successful")
    
    # Step 2: Set up rooms with tables
    print("\n2. Setting up rooms with tables...")
    if not setup_rooms_with_tables(token):
        print("❌ Failed to set up rooms with tables")
        return False
    
    # Step 3: Assign reservations to tables
    print("\n3. Assigning reservations to tables...")
    if not assign_reservations_to_tables(token):
        print("❌ Failed to assign reservations to tables")
        return False
    
    # Step 4: Test daily view
    print("\n4. Testing daily view...")
    if not test_daily_view(token):
        print("❌ Daily view test failed")
        return False
    
    print("\n🎉 Deployment completed successfully!")
    print("\nThe daily view should now be working properly with:")
    print("- Tables created for each room with appropriate capacities")
    print("- Existing reservations assigned to suitable tables")
    print("- Proper data structure for the frontend")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        sys.exit(1) 