#!/usr/bin/env python3
"""
Test script to verify the web interface is working
"""

import urllib.request
import json

def test_web_interface():
    print("🌐 Testing Web Interface")
    print("=" * 40)
    
    try:
        # Test the main page
        response, status = make_request("http://localhost:8000/")
        if status == 200:
            print("✓ Main page is accessible")
            if "The Castle Pub" in response:
                print("✓ HTML content is correct")
            else:
                print("⚠ HTML content may be incorrect")
        else:
            print(f"✗ Main page failed: {status}")
            
        # Test static files
        response, status = make_request("http://localhost:8000/static/styles.css")
        if status == 200:
            print("✓ CSS file is accessible")
        else:
            print(f"✗ CSS file failed: {status}")
            
        response, status = make_request("http://localhost:8000/static/script.js")
        if status == 200:
            print("✓ JavaScript file is accessible")
        else:
            print(f"✗ JavaScript file failed: {status}")
            
        # Test API endpoints
        response, status = make_request("http://localhost:8000/api/rooms")
        if status == 200:
            print("✓ API rooms endpoint is working")
        else:
            print(f"✗ API rooms endpoint failed: {status}")
            
    except Exception as e:
        print(f"✗ Error testing web interface: {e}")

def make_request(url):
    """Make HTTP request"""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8'), response.status
    except Exception as e:
        return str(e), None

if __name__ == "__main__":
    test_web_interface()
    print("\n🎉 Web interface testing completed!")
    print("🌐 Open your browser and visit: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs") 