#!/usr/bin/env python3
"""
Test admin panel API key creation directly
"""
import os
import requests
import sys

def test_admin_panel():
    """Test the admin panel functionality"""
    try:
        base_url = "http://localhost:5000"
        
        # Test health endpoint first
        print("1. Testing server health...")
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Server is running")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
        
        # Test admin login page
        print("\n2. Testing admin login page...")
        response = requests.get(f"{base_url}/admin/login")
        if response.status_code == 200:
            print("✅ Admin login page is accessible")
        else:
            print(f"❌ Admin login page failed: {response.status_code}")
            return False
        
        # Start a session and login
        print("\n3. Testing admin login...")
        session = requests.Session()
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        response = session.post(f"{base_url}/admin/login", data=login_data)
        if response.status_code == 200 and 'dashboard' in response.url:
            print("✅ Admin login successful")
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            return False
        
        # Test dashboard
        print("\n4. Testing admin dashboard...")
        response = session.get(f"{base_url}/admin/dashboard")
        if response.status_code == 200:
            print("✅ Admin dashboard is accessible")
        else:
            print(f"❌ Admin dashboard failed: {response.status_code}")
            return False
        
        # Test API keys page
        print("\n5. Testing API keys page...")
        response = session.get(f"{base_url}/admin/api-keys")
        if response.status_code == 200:
            print("✅ API keys page is accessible")
            print("   You can now try creating API keys in the web interface!")
        else:
            print(f"❌ API keys page failed: {response.status_code}")
            return False
        
        print(f"\n🎉 Admin panel is working correctly!")
        print(f"   URL: {base_url}/admin")
        print(f"   Username: admin")
        print(f"   Password: admin123")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on port 5000")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    test_admin_panel()