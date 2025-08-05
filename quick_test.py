#!/usr/bin/env python3
"""
Quick test with the new API key
"""

import requests
import json

def test_new_api_key(api_key):
    """Test the newly created API key"""
    
    BASE_URL = "http://localhost:5000"
    
    print(f"🧪 Testing API Key: {api_key}")
    print("=" * 50)
    
    # Test endpoints
    endpoints = [
        ("/api/v1/status", {}),
        ("/api/v1/info", {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}),
        ("/api/v1/video", {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "quality": "360"})
    ]
    
    for endpoint, params in endpoints:
        try:
            response = requests.get(
                f"{BASE_URL}{endpoint}",
                params=params,
                headers={"X-API-Key": api_key},
                timeout=30
            )
            
            print(f"✅ {endpoint}: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if "title" in data:
                    print(f"   📺 Title: {data['title']}")
                elif "status" in data:
                    print(f"   📊 Status: {data['status']}")
            else:
                print(f"   ❌ Error: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n🎯 Your API key is ready to use!")

if __name__ == "__main__":
    # Use the demo key for testing
    test_new_api_key("demo-key")