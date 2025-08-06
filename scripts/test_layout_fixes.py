#!/usr/bin/env python3
"""
Test script to verify layout fixes
"""

import requests
import json
from datetime import date

# Configuration
BASE_URL = "http://localhost:8000"
TEST_ROOM_ID = "test-room-1"
TEST_DATE = date.today().isoformat()

def test_layout_editor_data():
    """Test the layout editor data endpoint"""
    print("Testing layout editor data endpoint...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/layout/editor/{TEST_ROOM_ID}",
            params={"target_date": TEST_DATE}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Layout editor data loaded successfully")
            print(f"   - Room ID: {data.get('room_id')}")
            print(f"   - Tables count: {len(data.get('tables', []))}")
            print(f"   - Reservations count: {len(data.get('reservations', []))}")
            return True
        else:
            print(f"❌ Failed to load layout editor data: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing layout editor data: {e}")
        return False

def test_table_creation():
    """Test creating a new table layout"""
    print("\nTesting table creation...")
    
    table_data = {
        "table_id": "test-table-1",
        "room_id": TEST_ROOM_ID,
        "x_position": 100.0,
        "y_position": 100.0,
        "width": 100.0,
        "height": 80.0,
        "shape": "rectangular",
        "color": "#4A90E2",
        "border_color": "#2E5BBA",
        "text_color": "#FFFFFF",
        "show_capacity": True,
        "show_name": True,
        "font_size": 12,
        "custom_capacity": 4,
        "is_connected": False,
        "connected_to": None,
        "z_index": 1
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/layout/tables",
            json=table_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Table created successfully")
            print(f"   - Layout ID: {data.get('id')}")
            print(f"   - Table ID: {data.get('table_id')}")
            return data.get('id')
        else:
            print(f"❌ Failed to create table: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return None

def test_table_update(layout_id):
    """Test updating a table layout"""
    if not layout_id:
        print("❌ No layout ID provided for update test")
        return False
        
    print(f"\nTesting table update for layout {layout_id}...")
    
    update_data = {
        "x_position": 150.0,
        "y_position": 150.0
    }
    
    try:
        response = requests.put(
            f"{BASE_URL}/api/layout/tables/{layout_id}",
            json=update_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Table updated successfully")
            print(f"   - New position: ({data.get('x_position')}, {data.get('y_position')})")
            return True
        else:
            print(f"❌ Failed to update table: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating table: {e}")
        return False

def test_table_deletion(layout_id):
    """Test deleting a table layout"""
    if not layout_id:
        print("❌ No layout ID provided for deletion test")
        return False
        
    print(f"\nTesting table deletion for layout {layout_id}...")
    
    try:
        response = requests.delete(
            f"{BASE_URL}/api/layout/tables/{layout_id}"
        )
        
        if response.status_code == 200:
            print(f"✅ Table deleted successfully")
            return True
        else:
            print(f"❌ Failed to delete table: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error deleting table: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Layout System Fixes")
    print("=" * 50)
    
    # Test 1: Layout editor data loading
    success1 = test_layout_editor_data()
    
    # Test 2: Table creation
    layout_id = test_table_creation()
    
    # Test 3: Table update
    success3 = test_table_update(layout_id)
    
    # Test 4: Table deletion
    success4 = test_table_deletion(layout_id)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Layout Editor Data: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"   Table Creation: {'✅ PASS' if layout_id else '❌ FAIL'}")
    print(f"   Table Update: {'✅ PASS' if success3 else '❌ FAIL'}")
    print(f"   Table Deletion: {'✅ PASS' if success4 else '❌ FAIL'}")
    
    if all([success1, layout_id, success3, success4]):
        print("\n🎉 All tests passed! Layout system is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main() 