#!/usr/bin/env python3
"""
COMPREHENSIVE SYSTEM DEBUG - HEAD TO TOE ANALYSIS
This script will systematically test every layer of the system
"""

import os
import sys
import requests
import json
from datetime import datetime, date, timedelta

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_database_connection():
    """Test direct database connection and models"""
    print("🔍 TESTING DATABASE CONNECTION & MODELS")
    print("=" * 60)
    
    try:
        from app.core.database import SessionLocal, engine
        from app.models.room import Room
        from app.models.table import Table  
        from app.models.reservation import Reservation, ReservationTable
        from app.models.user import User
        from app.models.settings import RestaurantSettings, WorkingHours
        from sqlalchemy import text
        
        db = SessionLocal()
        
        # Test basic connection
        result = db.execute(text("SELECT 1")).fetchone()
        print("✅ Database connection successful")
        
        # Test each model individually
        models_to_test = [
            ("Room", Room),
            ("Table", Table),
            ("Reservation", Reservation),
            ("ReservationTable", ReservationTable), 
            ("User", User),
            ("RestaurantSettings", RestaurantSettings),
            ("WorkingHours", WorkingHours)
        ]
        
        for model_name, model_class in models_to_test:
            try:
                count = db.query(model_class).count()
                print(f"✅ {model_name:<20} | {count:>3} records")
            except Exception as e:
                print(f"❌ {model_name:<20} | ERROR: {e}")
        
        # Test specific relationships
        print("\n🔗 TESTING RELATIONSHIPS")
        print("-" * 30)
        
        # Room -> Tables relationship
        rooms = db.query(Room).all()
        for room in rooms[:2]:  # Test first 2 rooms
            table_count = len(room.tables) if hasattr(room, 'tables') else 0
            print(f"Room '{room.name}' has {table_count} tables")
        
        # Reservation -> ReservationTable relationship
        reservations = db.query(Reservation).limit(3).all()
        for res in reservations:
            rt_count = len(res.reservation_tables) if hasattr(res, 'reservation_tables') else 0
            print(f"Reservation '{res.customer_name}' has {rt_count} table assignments")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_api_endpoints():
    """Test all API endpoints systematically"""
    print("\n🌐 TESTING API ENDPOINTS")
    print("=" * 60)
    
    base_url = "https://reservationsystem-production-10cc.up.railway.app"
    
    endpoints = [
        # Core endpoints
        ("GET", "/", "Main page"),
        ("GET", "/health", "Health check"),
        ("GET", "/api", "API root"),
        
        # Admin endpoints (most critical)
        ("GET", "/admin/rooms", "Admin rooms"),
        ("GET", "/admin/tables", "Admin tables"), 
        ("GET", "/admin/reservations", "Admin reservations"),
        
        # Settings endpoints
        ("GET", "/api/settings/rooms", "Settings rooms"),
        ("GET", "/api/settings/restaurant", "Restaurant settings"),
        ("GET", "/api/settings/working-hours", "Working hours"),
        
        # Dashboard endpoints
        ("GET", "/api/dashboard/stats", "Dashboard stats"),
        ("GET", "/api/dashboard/notes", "Dashboard notes"),
        ("GET", "/api/dashboard/customers", "Dashboard customers"),
        ("GET", "/api/dashboard/today", "Dashboard today"),
        
        # Layout endpoints
        ("GET", f"/api/layout/daily/{date.today().isoformat()}", "Daily layout"),
        
        # Auth endpoints (expect 405 for GET)
        ("GET", "/auth/login", "Auth login"),
        ("GET", "/api/auth/login", "API auth login"),
    ]
    
    results = []
    
    for method, endpoint, description in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, timeout=10)
                
            status = response.status_code
            
            # Determine if this is expected
            expected = status == 200 or (endpoint.endswith("/login") and status == 405)
            
            symbol = "✅" if expected else "❌"
            status_text = f"{status}"
            
            print(f"{symbol} {description:<25} | {status_text:>3} | {endpoint}")
            
            # Get response size/type for successful responses
            if status == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"    └─ Returns {len(data)} items")
                    elif isinstance(data, dict):
                        keys = list(data.keys())[:3]
                        print(f"    └─ Returns object: {keys}...")
                except:
                    print(f"    └─ Returns non-JSON data ({len(response.content)} bytes)")
            
            results.append((endpoint, status, expected))
            
        except requests.exceptions.Timeout:
            print(f"❌ {description:<25} | TIMEOUT | {endpoint}")
            results.append((endpoint, "TIMEOUT", False))
        except Exception as e:
            print(f"❌ {description:<25} | ERROR | {endpoint} ({e})")
            results.append((endpoint, "ERROR", False))
    
    # Summary
    total = len(results)
    working = sum(1 for _, _, expected in results if expected)
    print(f"\n📊 ENDPOINT SUMMARY: {working}/{total} working ({working/total*100:.1f}%)")
    
    return results

def test_specific_issues():
    """Test specific reported issues"""
    print("\n🐛 TESTING SPECIFIC REPORTED ISSUES")
    print("=" * 60)
    
    base_url = "https://reservationsystem-production-10cc.up.railway.app"
    
    # Test reservation editing endpoint that was causing 500 error
    print("Testing reservation editing...")
    try:
        # First get reservations to find a valid ID
        reservations_response = requests.get(f"{base_url}/admin/reservations")
        if reservations_response.status_code == 200:
            reservations = reservations_response.json()
            if reservations:
                test_id = reservations[0].get('id')
                if test_id:
                    edit_response = requests.get(f"{base_url}/admin/reservations/{test_id}")
                    print(f"✅ Reservation editing: {edit_response.status_code}")
                    if edit_response.status_code == 200:
                        print("    └─ Reservation details loaded successfully")
                    else:
                        print(f"    └─ ERROR: {edit_response.status_code} - {edit_response.text[:100]}")
                else:
                    print("❌ No reservation ID found")
            else:
                print("❌ No reservations found")
        else:
            print(f"❌ Could not fetch reservations: {reservations_response.status_code}")
    except Exception as e:
        print(f"❌ Reservation editing test failed: {e}")
    
    # Test daily layout with specific date
    print("\nTesting daily layout...")
    try:
        today = date.today().isoformat()
        response = requests.get(f"{base_url}/api/layout/daily/{today}")
        print(f"✅ Daily layout: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            rooms = data.get('rooms', [])
            print(f"    └─ {len(rooms)} rooms returned")
            for room in rooms[:2]:
                tables = room.get('tables', [])
                print(f"    └─ Room '{room.get('name')}': {len(tables)} tables")
                # Check if any table has reservations array
                for table in tables[:1]:
                    reservations = table.get('reservations', 'MISSING')
                    if reservations == 'MISSING':
                        print(f"    └─ ❌ Table missing reservations array!")
                    else:
                        print(f"    └─ ✅ Table has reservations array ({len(reservations)} items)")
    except Exception as e:
        print(f"❌ Daily layout test failed: {e}")
    
    # Test notes creation
    print("\nTesting notes creation...")
    try:
        note_data = {"content": "Test note from debug script", "created_by": "debug_script"}
        response = requests.post(f"{base_url}/api/dashboard/notes", json=note_data)
        print(f"✅ Notes creation: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"    └─ Created note ID: {result.get('id')}")
    except Exception as e:
        print(f"❌ Notes creation test failed: {e}")

def main():
    """Run comprehensive system debug"""
    print("🚀 COMPREHENSIVE SYSTEM DEBUG - HEAD TO TOE")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Test 1: Database layer
    db_ok = test_database_connection()
    
    # Test 2: API layer  
    api_results = test_api_endpoints()
    
    # Test 3: Specific issues
    test_specific_issues()
    
    # Final summary
    print("\n" + "=" * 80)
    print("🎯 FINAL DIAGNOSIS")
    print("=" * 80)
    
    if db_ok:
        print("✅ Database layer: WORKING")
    else:
        print("❌ Database layer: BROKEN")
    
    api_working = sum(1 for _, _, ok in api_results if ok)
    api_total = len(api_results)
    
    if api_working / api_total > 0.8:
        print("✅ API layer: MOSTLY WORKING")
    elif api_working / api_total > 0.5:
        print("⚠️  API layer: PARTIAL ISSUES")
    else:
        print("❌ API layer: MAJOR ISSUES")
    
    print(f"\nNext steps:")
    print(f"1. If database issues: Check Railway DB connection")
    print(f"2. If API issues: Check specific endpoint logs")
    print(f"3. If frontend issues: Check browser console for JS errors")

if __name__ == "__main__":
    main()