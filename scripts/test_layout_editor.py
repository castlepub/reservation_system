#!/usr/bin/env python3
"""
Script to test the layout editor endpoint on Railway
"""
import os
import sys
import requests
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_layout_editor():
    """Test the layout editor endpoint on Railway"""
    
    # Test the layout editor endpoint on Railway
    room_id = "550e8400-e29b-41d4-a716-446655440001"  # Front Room
    target_date = "2025-08-05"
    
    url = f"https://reservationsystem-production-10cc.up.railway.app/api/layout/editor/{room_id}?target_date={target_date}"
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Room: {data['room']['name']}")
            print(f"Number of tables: {len(data['tables'])}")
            
            print("\nTable data:")
            for table in data['tables']:
                print(f"  Table: {table['table_name']}")
                print(f"    Table ID: {table['table_id']}")
                print(f"    Layout ID: {table['layout_id']}")
                print(f"    Position: ({table['x_position']}, {table['y_position']})")
                print()
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error testing endpoint: {e}")

if __name__ == "__main__":
    test_layout_editor()