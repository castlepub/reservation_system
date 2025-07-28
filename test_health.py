#!/usr/bin/env python3
"""
Test script for health check endpoint
"""

import requests
import time
import sys

def test_health_check(base_url="http://localhost:8000"):
    """Test the health check endpoint"""
    try:
        print(f"Testing health check at: {base_url}/health")
        
        response = requests.get(f"{base_url}/health", timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✓ Health check passed!")
            return True
        else:
            print("✗ Health check failed!")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Connection error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def wait_for_service(base_url="http://localhost:8000", max_attempts=30):
    """Wait for service to become available"""
    print(f"Waiting for service at {base_url}...")
    
    for attempt in range(max_attempts):
        print(f"Attempt {attempt + 1}/{max_attempts}...")
        
        if test_health_check(base_url):
            return True
            
        time.sleep(2)
    
    print("Service did not become available in time")
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    
    if "--wait" in sys.argv:
        success = wait_for_service(base_url)
        sys.exit(0 if success else 1)
    else:
        success = test_health_check(base_url)
        sys.exit(0 if success else 1) 