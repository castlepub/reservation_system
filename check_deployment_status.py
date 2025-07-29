#!/usr/bin/env python3
"""
Diagnostic script to check Railway deployment status
"""

import requests
import time
import os

def check_railway_deployment():
    """Check if the Railway deployment is working"""
    
    # Get the Railway URL from environment or ask user
    railway_url = os.getenv('RAILWAY_URL')
    if not railway_url:
        print("❌ RAILWAY_URL not found in environment")
        print("Please set RAILWAY_URL environment variable or provide it manually")
        railway_url = input("Enter your Railway URL (e.g., https://your-app.railway.app): ").strip()
    
    if not railway_url:
        print("❌ No URL provided")
        return
    
    # Remove trailing slash
    railway_url = railway_url.rstrip('/')
    
    print(f"🔍 Checking Railway deployment at: {railway_url}")
    print("=" * 50)
    
    # Test endpoints
    endpoints = [
        ("/ping", "Ultra simple ping"),
        ("/health/simple", "Simple health check"),
        ("/health", "Full health check"),
        ("/", "Main page"),
        ("/api", "API root"),
        ("/docs", "API documentation")
    ]
    
    for endpoint, description in endpoints:
        url = f"{railway_url}{endpoint}"
        print(f"\n🔗 Testing {description}: {url}")
        
        try:
            start_time = time.time()
            response = requests.get(url, timeout=10)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            if response.status_code == 200:
                print(f"✅ Status: {response.status_code} (Response time: {response_time:.0f}ms)")
                
                # Show response content for ping endpoint
                if endpoint == "/ping":
                    print(f"   Response: {response.text}")
                elif endpoint == "/health":
                    try:
                        health_data = response.json()
                        print(f"   Status: {health_data.get('status', 'unknown')}")
                        print(f"   Database: {health_data.get('database', 'unknown')}")
                    except:
                        print(f"   Response: {response.text[:100]}...")
                        
            else:
                print(f"❌ Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout (10s) - Service might be starting up")
        except requests.exceptions.ConnectionError:
            print(f"🔌 Connection Error - Service might not be running")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("📋 Troubleshooting Tips:")
    print("1. If all endpoints fail: Check Railway dashboard for deployment status")
    print("2. If only some endpoints fail: Check application logs in Railway")
    print("3. If ping works but others don't: Database connection issue")
    print("4. If health check shows 'degraded': Database is slow to connect")
    print("5. Check Railway logs for startup errors")

if __name__ == "__main__":
    check_railway_deployment() 