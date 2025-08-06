#!/usr/bin/env python3
import requests
import json

# Test Rick Astley video that user manually uploaded
url = "http://localhost:5000/api/v1/video"
params = {
    'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    'quality': '360p',
    'api_key': 'test_api_key_12345'
}

print("🎯 Testing Rick Astley Video API...")
print(f"URL: {url}")
print(f"Parameters: {params}")
print()

try:
    response = requests.get(url, params=params, timeout=60)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print()
    
    if response.status_code == 200:
        data = response.json()
        print("✅ API Response:")
        print(json.dumps(data, indent=2))
        
        # Check if it used cached content
        if data.get('cached'):
            print("\n🎉 SUCCESS! Used cached content!")
            print(f"Source: {data.get('source', 'unknown')}")
            print(f"Response Time: {data.get('response_time', 'N/A')}")
        else:
            print(f"\n⚠️ Not cached, used source: {data.get('source', 'unknown')}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ Request failed: {e}")