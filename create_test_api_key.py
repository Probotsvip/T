#!/usr/bin/env python3
"""
Simple script to create and test API key
"""

import requests
import json
import uuid
from datetime import datetime

def test_api_with_demo_key():
    """Test API endpoints with demo key"""
    
    BASE_URL = "http://localhost:5000"
    API_KEY = "demo-key"
    
    print("🧪 Testing YouTube API with demo key")
    print("=" * 40)
    
    # Test 1: Server status
    print("1. Server Status:")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/status?api_key={API_KEY}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {data.get('status')}")
            print(f"   ✅ Concurrent users: {data.get('concurrent_users', 0)}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Video info
    print("\n2. Video Information:")
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/info",
            params={"url": test_url, "api_key": API_KEY},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Title: {data.get('title', 'N/A')}")
            print(f"   ✅ Duration: {data.get('duration', 0)} seconds")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   Response: {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Video download
    print("\n3. Video Download:")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/video",
            params={"url": test_url, "quality": "360", "api_key": API_KEY},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {data.get('status')}")
            if 'download_url' in data:
                print(f"   ✅ Download URL: {data['download_url'][:50]}...")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   Response: {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Audio download
    print("\n4. Audio Download:")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/audio",
            params={"url": test_url, "api_key": API_KEY},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {data.get('status')}")
            if 'download_url' in data:
                print(f"   ✅ Download URL: {data['download_url'][:50]}...")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   Response: {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print(f"\n🎉 API Key Testing Completed!")
    print(f"📝 Your API key: demo-key")
    print(f"🔗 Admin panel: {BASE_URL}/admin")
    print(f"📖 Full documentation: USAGE.md")
    
    return True

if __name__ == "__main__":
    test_api_with_demo_key()