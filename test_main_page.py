#!/usr/bin/env python3
"""
Test the main page content
"""

import urllib.request
import urllib.parse

def test_main_page():
    print("🌐 Testing Main Page Content")
    print("=" * 40)
    
    try:
        # Test the main page
        response = urllib.request.urlopen('http://localhost:8000/')
        content = response.read().decode('utf-8')
        
        print(f"Status: {response.status}")
        print(f"Content length: {len(content)} characters")
        
        # Check for key content
        checks = [
            ("The Castle Pub", "Title"),
            ("reservation", "Reservation system"),
            ("admin", "Admin section"),
            ("castle-illustration", "Castle icon"),
            ("btn-primary", "Primary buttons"),
            ("hero", "Hero section")
        ]
        
        for text, description in checks:
            if text in content:
                print(f"✅ {description}: Found")
            else:
                print(f"❌ {description}: Not found")
        
        # Show first 500 characters
        print(f"\nFirst 500 characters:")
        print("-" * 40)
        print(content[:500])
        print("-" * 40)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_main_page() 