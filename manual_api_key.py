#!/usr/bin/env python3
"""
Manual API Key Generator and Tester
"""

import uuid
import requests

def generate_api_key():
    """Generate a simple API key"""
    return f"api_{uuid.uuid4().hex[:24]}"

def test_api_key(api_key):
    """Test API key with all endpoints"""
    
    BASE_URL = "http://localhost:5000"
    
    print(f"🔑 Your New API Key: {api_key}")
    print("=" * 60)
    
    # Test endpoints
    endpoints = [
        {
            "name": "Server Status",
            "url": f"{BASE_URL}/api/v1/status",
            "params": {"api_key": api_key}
        },
        {
            "name": "Video Info",
            "url": f"{BASE_URL}/api/v1/info",
            "params": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "api_key": api_key
            }
        },
        {
            "name": "Video Download",
            "url": f"{BASE_URL}/api/v1/video",
            "params": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "quality": "360",
                "api_key": api_key
            }
        },
        {
            "name": "Audio Download",
            "url": f"{BASE_URL}/api/v1/audio",
            "params": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "api_key": api_key
            }
        }
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\n🧪 Testing {endpoint['name']}...")
            response = requests.get(endpoint["url"], params=endpoint["params"], timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success: {response.status_code}")
                
                if "title" in data:
                    print(f"   📺 Title: {data['title']}")
                elif "status" in data:
                    print(f"   📊 Status: {data['status']}")
                if "download_url" in data:
                    print(f"   🔗 Download: Available")
                    
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   Response: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n🎯 API Key Testing Complete!")
    print(f"📝 Your API Key: {api_key}")
    print(f"📖 Usage Examples:")
    print(f"   • Headers: X-API-Key: {api_key}")
    print(f"   • URL param: ?api_key={api_key}")
    print(f"   • See USAGE.md for full documentation")

def main():
    """Main function"""
    print("YouTube API Key Generator")
    print("=" * 30)
    
    # Generate new API key
    new_api_key = generate_api_key()
    
    # Test the API key
    test_api_key(new_api_key)

if __name__ == "__main__":
    main()