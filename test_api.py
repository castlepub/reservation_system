#!/usr/bin/env python3
"""
Test script to verify The Castle Pub Reservation System API
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✓ Health endpoint working")
            print(f"  Response: {response.json()}")
        else:
            print(f"✗ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Health endpoint error: {e}")

def test_root():
    """Test root endpoint"""
    print("\n🏠 Testing root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✓ Root endpoint working")
            print(f"  Response: {response.json()}")
        else:
            print(f"✗ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Root endpoint error: {e}")

def test_rooms():
    """Test rooms endpoint"""
    print("\n🏛️ Testing rooms endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/rooms")
        if response.status_code == 200:
            rooms = response.json()
            print("✓ Rooms endpoint working")
            print(f"  Found {len(rooms)} rooms:")
            for room in rooms:
                print(f"    - {room['name']}: {room['description']}")
        else:
            print(f"✗ Rooms endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Rooms endpoint error: {e}")

def test_availability():
    """Test availability endpoint"""
    print("\n📅 Testing availability endpoint...")
    try:
        # Test for tomorrow
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        response = requests.get(f"{BASE_URL}/api/availability", params={
            "date": tomorrow,
            "party_size": 4
        })
        if response.status_code == 200:
            availability = response.json()
            print("✓ Availability endpoint working")
            print(f"  Date: {availability['date']}")
            print(f"  Party size: {availability['party_size']}")
            print(f"  Available slots: {len(availability['available_slots'])}")
        else:
            print(f"✗ Availability endpoint failed: {response.status_code}")
            print(f"  Response: {response.text}")
    except Exception as e:
        print(f"✗ Availability endpoint error: {e}")

def test_auth():
    """Test authentication"""
    print("\n🔐 Testing authentication...")
    try:
        # Test login with default admin credentials
        response = requests.post(f"{BASE_URL}/api/auth/login", data={
            "username": "admin",
            "password": "admin123"
        })
        if response.status_code == 200:
            token_data = response.json()
            print("✓ Authentication working")
            print(f"  Token type: {token_data['token_type']}")
            print(f"  User: {token_data['user']['username']} ({token_data['user']['role']})")
            return token_data['access_token']
        else:
            print(f"✗ Authentication failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
    except Exception as e:
        print(f"✗ Authentication error: {e}")
        return None

def test_admin_endpoints(token):
    """Test admin endpoints"""
    if not token:
        print("⚠️ Skipping admin endpoints (no token)")
        return
    
    print("\n👑 Testing admin endpoints...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Test admin rooms endpoint
        response = requests.get(f"{BASE_URL}/api/admin/rooms", headers=headers)
        if response.status_code == 200:
            rooms = response.json()
            print("✓ Admin rooms endpoint working")
            print(f"  Found {len(rooms)} rooms")
        else:
            print(f"✗ Admin rooms endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Admin rooms endpoint error: {e}")

def main():
    print("🏰 The Castle Pub Reservation System - API Test")
    print("=" * 50)
    
    # Test basic endpoints
    test_health()
    test_root()
    test_rooms()
    test_availability()
    
    # Test authentication
    token = test_auth()
    
    # Test admin endpoints
    test_admin_endpoints(token)
    
    print("\n" + "=" * 50)
    print("🎉 API testing completed!")
    print(f"📚 API Documentation: {BASE_URL}/docs")
    print(f"📖 ReDoc Documentation: {BASE_URL}/redoc")

if __name__ == "__main__":
    main() 