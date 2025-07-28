#!/usr/bin/env python3
"""
Simple test script for The Castle Pub Reservation System
"""

import urllib.request
import urllib.parse
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def make_request(url, method="GET", data=None):
    """Make HTTP request"""
    try:
        if data and method == "POST":
            data = urllib.parse.urlencode(data).encode('utf-8')
            req = urllib.request.Request(url, data=data, method=method)
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        else:
            req = urllib.request.Request(url, method=method)
        
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8'), response.status
    except Exception as e:
        return str(e), None

def test_health():
    """Test health endpoint"""
    print("🏥 Testing health endpoint...")
    response, status = make_request(f"{BASE_URL}/health")
    if status == 200:
        print("✓ Health endpoint working")
        print(f"  Response: {response}")
    else:
        print(f"✗ Health endpoint failed: {status}")

def test_root():
    """Test root endpoint"""
    print("\n🏠 Testing root endpoint...")
    response, status = make_request(f"{BASE_URL}/")
    if status == 200:
        print("✓ Root endpoint working")
        print(f"  Response: {response}")
    else:
        print(f"✗ Root endpoint failed: {status}")

def test_rooms():
    """Test rooms endpoint"""
    print("\n🏛️ Testing rooms endpoint...")
    response, status = make_request(f"{BASE_URL}/api/rooms")
    if status == 200:
        print("✓ Rooms endpoint working")
        try:
            rooms = json.loads(response)
            print(f"  Found {len(rooms)} rooms:")
            for room in rooms:
                print(f"    - {room['name']}: {room['description']}")
        except:
            print(f"  Response: {response}")
    else:
        print(f"✗ Rooms endpoint failed: {status}")

def main():
    print("🏰 The Castle Pub Reservation System - Simple Test")
    print("=" * 50)
    
    # Test basic endpoints
    test_health()
    test_root()
    test_rooms()
    
    print("\n" + "=" * 50)
    print("🎉 Basic testing completed!")
    print(f"📚 API Documentation: {BASE_URL}/docs")
    print(f"📖 ReDoc Documentation: {BASE_URL}/redoc")
    print("\n🔑 To test admin features, visit the docs and login with:")
    print("   Username: admin")
    print("   Password: admin123")

if __name__ == "__main__":
    main() 