#!/usr/bin/env python3
"""
Script to test the PUT endpoint for table layout updates
"""
import requests
import json

def test_put_endpoint():
    """Test the PUT endpoint for table layout updates"""
    
    # Test the PUT endpoint with the new layout ID for F1
    layout_id = "3a5f656a-57cf-4b51-9aaa-0d05bf401194"  # F1 layout ID from the new response
    
    url = f"https://reservationsystem-production-10cc.up.railway.app/api/layout/tables/{layout_id}"
    
    # Test data
    position_data = {
        "x_position": 200,
        "y_position": 200
    }
    
    try:
        response = requests.put(url, json=position_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data}")
        elif response.status_code == 404:
            print(f"404 Not Found: Layout ID {layout_id} not found")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error testing PUT endpoint: {e}")

if __name__ == "__main__":
    test_put_endpoint() 