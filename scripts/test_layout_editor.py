#!/usr/bin/env python3
"""
Test script to check layout editor API response and identify table selection issues
"""

import requests
import json
from datetime import datetime

# API base URL
API_BASE_URL = "https://reservationsystem-production-10cc.up.railway.app"

def test_layout_editor():
    """Test the layout editor endpoint for all rooms"""
    try:
        # Test date
        test_date = datetime.now().strftime("%Y-%m-%d")
        
        # First get all rooms
        rooms_url = f"{API_BASE_URL}/admin/rooms"
        print(f"Getting rooms from: {rooms_url}")
        
        rooms_response = requests.get(rooms_url)
        print(f"Rooms response status: {rooms_response.status_code}")
        
        if rooms_response.status_code != 200:
            print("❌ Failed to get rooms")
            return
            
        rooms = rooms_response.json()
        print(f"Found {len(rooms)} rooms")
        
        for room in rooms:
            room_id = room.get('id')
            room_name = room.get('name', 'Unknown')
            print(f"\n🏠 Testing Layout Editor for: {room_name} (ID: {room_id})")
            
            # Test layout editor endpoint
            layout_url = f"{API_BASE_URL}/api/layout/editor/{room_id}?target_date={test_date}"
            print(f"Layout URL: {layout_url}")
            
            layout_response = requests.get(layout_url)
            print(f"Layout response status: {layout_response.status_code}")
            
            if layout_response.status_code == 200:
                layout_data = layout_response.json()
                print(f"✅ Layout editor response received")
                
                # Check for duplicate table IDs
                table_ids = []
                tables = layout_data.get('tables', [])
                print(f"Tables count: {len(tables)}")
                
                duplicate_ids = []
                for table in tables:
                    table_id = table.get('table_id')
                    layout_id = table.get('layout_id')
                    table_name = table.get('table_name')
                    
                    if table_id in table_ids:
                        duplicate_ids.append(table_id)
                        print(f"⚠️  DUPLICATE TABLE ID: {table_id} ({table_name})")
                    else:
                        table_ids.append(table_id)
                    
                    print(f"  - Table: {table_name} (table_id: {table_id}, layout_id: {layout_id})")
                    
                    # Check for missing or problematic properties
                    if not table_id:
                        print(f"❌ Missing table_id for table: {table_name}")
                    if not layout_id:
                        print(f"❌ Missing layout_id for table: {table_name}")
                    if table_id != layout_id:
                        print(f"⚠️  table_id ({table_id}) != layout_id ({layout_id}) for {table_name}")
                
                if duplicate_ids:
                    print(f"❌ FOUND DUPLICATE TABLE IDs: {duplicate_ids}")
                    print("This could cause table selection issues!")
                else:
                    print("✅ No duplicate table IDs found")
                    
            else:
                print(f"❌ Layout editor failed with status {layout_response.status_code}")
                if layout_response.status_code == 404:
                    print("Room not found or endpoint missing")
                
    except Exception as e:
        print(f"❌ Error testing layout editor: {e}")

if __name__ == "__main__":
    print("Testing Layout Editor API")
    print("=" * 50)
    test_layout_editor()