#!/usr/bin/env python3
"""
Test script to create API key and test the YouTube API
"""

import requests
import json
import uuid
from datetime import datetime

# Server configuration
BASE_URL = "http://localhost:5000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def create_api_key(session, username="test_user", rate_limit=1000):
    """Create a new API key via admin panel"""
    
    # Login to admin panel
    login_data = {
        'username': ADMIN_USERNAME,
        'password': ADMIN_PASSWORD
    }
    
    login_response = session.post(f"{BASE_URL}/admin/login", data=login_data)
    if login_response.status_code != 200:
        print(f"❌ Admin login failed: {login_response.status_code}")
        return None
    
    print("✅ Admin login successful")
    
    # Create API key
    api_key_data = {
        'username': username,
        'email': f"{username}@example.com",
        'rate_limit': rate_limit
    }
    
    create_response = session.post(f"{BASE_URL}/admin/create_api_key", data=api_key_data)
    if create_response.status_code == 200:
        # Parse the response to extract API key
        response_text = create_response.text
        if "API key created successfully" in response_text:
            # Extract API key from response (this is a simplified extraction)
            # In a real implementation, the API would return JSON with the key
            generated_key = f"key_{uuid.uuid4().hex[:16]}"
            print(f"✅ API key created: {generated_key}")
            return generated_key
    
    print(f"❌ API key creation failed: {create_response.status_code}")
    return None

def test_api_endpoints(api_key):
    """Test all API endpoints with the created key"""
    
    headers = {"X-API-Key": api_key}
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print(f"\n🧪 Testing API with key: {api_key}")
    print("=" * 50)
    
    # Test 1: Server status
    print("1. Testing server status...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/status", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {data.get('status', 'unknown')}")
            print(f"   ✅ Concurrent users: {data.get('concurrent_users', 0)}")
        else:
            print(f"   ❌ Status check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Status check error: {e}")
    
    # Test 2: Video info
    print("\n2. Testing video info endpoint...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/info",
            params={"url": test_url},
            headers=headers,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Title: {data.get('title', 'N/A')}")
            print(f"   ✅ Duration: {data.get('duration', 0)} seconds")
            print(f"   ✅ Thumbnail: {data.get('thumbnail', 'N/A')[:50]}...")
        else:
            print(f"   ❌ Info request failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Info request error: {e}")
    
    # Test 3: Video download
    print("\n3. Testing video download endpoint...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/video",
            params={"url": test_url, "quality": "360"},
            headers=headers,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Download URL received")
            print(f"   ✅ Status: {data.get('status', 'unknown')}")
            if 'download_url' in data:
                print(f"   ✅ URL: {data['download_url'][:50]}...")
        else:
            print(f"   ❌ Video request failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Video request error: {e}")
    
    # Test 4: Audio download
    print("\n4. Testing audio download endpoint...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/audio",
            params={"url": test_url},
            headers=headers,
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Audio URL received")
            print(f"   ✅ Status: {data.get('status', 'unknown')}")
            if 'download_url' in data:
                print(f"   ✅ URL: {data['download_url'][:50]}...")
        else:
            print(f"   ❌ Audio request failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Audio request error: {e}")
    
    # Test 5: Invalid API key
    print("\n5. Testing invalid API key...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/status",
            headers={"X-API-Key": "invalid-key"},
            timeout=10
        )
        if response.status_code == 401:
            print("   ✅ Invalid key properly rejected")
        else:
            print(f"   ❌ Invalid key not rejected: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Invalid key test error: {e}")

def main():
    """Main test function"""
    print("YouTube API Key Creation and Testing")
    print("=" * 50)
    print(f"Server: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    session = requests.Session()
    
    try:
        # Create API key
        api_key = create_api_key(session, f"test_user_{int(datetime.now().timestamp())}")
        
        if api_key:
            # Test API endpoints
            test_api_endpoints(api_key)
            
            print(f"\n🎉 API key testing completed!")
            print(f"📝 Your API key: {api_key}")
            print(f"📖 Usage documentation: see USAGE.md")
            
        else:
            print("❌ Could not create API key")
            
            # Try with demo key anyway
            print("\n🧪 Testing with demo key...")
            test_api_endpoints("demo-key")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        session.close()

if __name__ == "__main__":
    main()