#!/usr/bin/env python3
"""
Comprehensive system status check - validate all functionality
"""

import requests
import json
from datetime import datetime, date, timedelta

# API base URL
API_BASE_URL = "https://reservationsystem-production-10cc.up.railway.app"

def test_endpoint(name, url, expected_status=200, show_data=False):
    """Test an endpoint and return status"""
    try:
        response = requests.get(url)
        status = "✅ WORKING" if response.status_code == expected_status else f"❌ ERROR ({response.status_code})"
        print(f"{name:<35} | {status}")
        
        if show_data and response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"  └─ Returns {len(data)} items")
            elif isinstance(data, dict):
                print(f"  └─ Returns object with keys: {list(data.keys())[:5]}")
        
        return response.status_code == expected_status
    except Exception as e:
        print(f"{name:<35} | ❌ EXCEPTION: {e}")
        return False

def comprehensive_status_check():
    """Run comprehensive system check"""
    print("🔍 COMPREHENSIVE SYSTEM STATUS CHECK")
    print("=" * 80)
    print()
    
    total_tests = 0
    passed_tests = 0
    
    # Core endpoints
    print("📊 CORE ENDPOINTS")
    print("-" * 50)
    
    endpoints = [
        ("Health Check", f"{API_BASE_URL}/health"),
        ("API Root", f"{API_BASE_URL}/api"),
        ("Main App", f"{API_BASE_URL}/", 200),
    ]
    
    for name, url, *expected in endpoints:
        expected_status = expected[0] if expected else 200
        if test_endpoint(name, url, expected_status):
            passed_tests += 1
        total_tests += 1
    
    print()
    
    # Authentication endpoints
    print("🔐 AUTHENTICATION")
    print("-" * 50)
    
    auth_endpoints = [
        ("Login (Auth)", f"{API_BASE_URL}/auth/login"),
        ("Login (API)", f"{API_BASE_URL}/api/auth/login"),
        ("Auth Me", f"{API_BASE_URL}/auth/me"),
        ("API Auth Me", f"{API_BASE_URL}/api/auth/me"),
    ]
    
    for name, url in auth_endpoints:
        # POST endpoints might return 405 for GET, that's expected
        if test_endpoint(name, url, expected_status=405):
            passed_tests += 1
        total_tests += 1
    
    print()
    
    # Admin endpoints
    print("👑 ADMIN ENDPOINTS")
    print("-" * 50)
    
    admin_endpoints = [
        ("Admin Rooms", f"{API_BASE_URL}/admin/rooms", True),
        ("Admin Tables", f"{API_BASE_URL}/admin/tables", True),
        ("Admin Reservations", f"{API_BASE_URL}/admin/reservations", True),
    ]
    
    for name, url, show_data in admin_endpoints:
        if test_endpoint(name, url, show_data=show_data):
            passed_tests += 1
        total_tests += 1
    
    print()
    
    # Settings endpoints
    print("⚙️  SETTINGS ENDPOINTS")
    print("-" * 50)
    
    settings_endpoints = [
        ("Settings Rooms", f"{API_BASE_URL}/api/settings/rooms", True),
        ("Settings Restaurant", f"{API_BASE_URL}/api/settings/restaurant"),
        ("Working Hours", f"{API_BASE_URL}/api/settings/working-hours"),
    ]
    
    for name, url, *show_data in settings_endpoints:
        show = show_data[0] if show_data else False
        if test_endpoint(name, url, show_data=show):
            passed_tests += 1
        total_tests += 1
    
    print()
    
    # Dashboard endpoints
    print("📈 DASHBOARD ENDPOINTS")
    print("-" * 50)
    
    dashboard_endpoints = [
        ("Dashboard Today", f"{API_BASE_URL}/api/dashboard/today", True),
        ("Dashboard Stats", f"{API_BASE_URL}/api/dashboard/stats"),
        ("Dashboard Notes", f"{API_BASE_URL}/api/dashboard/notes", True),
        ("Dashboard Customers", f"{API_BASE_URL}/api/dashboard/customers", True),
    ]
    
    for name, url, *show_data in dashboard_endpoints:
        show = show_data[0] if show_data else False
        if test_endpoint(name, url, show_data=show):
            passed_tests += 1
        total_tests += 1
    
    print()
    
    # Layout endpoints
    print("🗺️  LAYOUT ENDPOINTS")
    print("-" * 50)
    
    today = datetime.now().strftime("%Y-%m-%d")
    layout_endpoints = [
        ("Daily Layout", f"{API_BASE_URL}/api/layout/daily/{today}", True),
        ("Layout Editor (Front Room)", f"{API_BASE_URL}/api/layout/editor/550e8400-e29b-41d4-a716-446655440001?target_date={today}", True),
    ]
    
    for name, url, show_data in layout_endpoints:
        if test_endpoint(name, url, show_data=show_data):
            passed_tests += 1
        total_tests += 1
    
    print()
    
    # Reservations endpoints
    print("📅 RESERVATIONS ENDPOINTS")
    print("-" * 50)
    
    reservations_endpoints = [
        ("Public Reservations", f"{API_BASE_URL}/api/reservations"),
        ("Available Tables", f"{API_BASE_URL}/api/tables/available"),
    ]
    
    for name, url in reservations_endpoints:
        if test_endpoint(name, url):
            passed_tests += 1
        total_tests += 1
    
    print()
    
    # Summary
    print("📋 SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("🎉 SYSTEM STATUS: EXCELLENT")
    elif success_rate >= 75:
        print("✅ SYSTEM STATUS: GOOD")
    elif success_rate >= 50:
        print("⚠️  SYSTEM STATUS: NEEDS ATTENTION")
    else:
        print("❌ SYSTEM STATUS: CRITICAL ISSUES")
    
    print()
    print("🎯 NEXT STEPS:")
    if total_tests - passed_tests > 0:
        print("- Fix failed endpoints above")
        print("- Test frontend functionality manually")
        print("- Check browser console for JavaScript errors")
    else:
        print("- All backend endpoints working!")
        print("- Frontend issues may require JavaScript debugging")
        print("- Consider checking browser developer tools")

if __name__ == "__main__":
    comprehensive_status_check()