#!/usr/bin/env python3
import requests
import time
import json

API_KEY = "ytapi_6e2883aa716b4c5d"
RICK_ASTLEY_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
BASE_URL = "http://localhost:5000/api/v1/video"

def test_cache_performance():
    """Test if cache system achieves 0.3s response time"""
    print("🚀 Testing Cache Performance for Rick Astley Video")
    print("=" * 60)
    
    params = {
        'url': RICK_ASTLEY_URL,
        'quality': '360p',
        'api_key': API_KEY
    }
    
    # Test multiple requests
    for i in range(3):
        print(f"\n📡 Request #{i+1}")
        start_time = time.time()
        
        try:
            response = requests.get(BASE_URL, params=params, timeout=60)
            end_time = time.time()
            response_time = end_time - start_time
            
            print(f"   Status: {response.status_code}")
            print(f"   Response Time: {response_time:.3f}s")
            
            if response.status_code == 200:
                data = response.json()
                cached = data.get('cached', False)
                source = data.get('source', 'unknown')
                
                print(f"   Cached: {cached}")
                print(f"   Source: {source}")
                
                if cached and response_time <= 0.3:
                    print("   🎉 PERFECT! Ultra-fast cache response!")
                elif cached:
                    print(f"   ✅ Cached but slow ({response_time:.3f}s)")
                else:
                    print("   ⚠️  Not cached, external source used")
                    
                # Show download URL
                download_url = data.get('download_url', 'N/A')
                if 'telegram' in download_url.lower():
                    print("   📱 Using Telegram CDN - EXCELLENT!")
                else:
                    print(f"   🌐 External CDN: {download_url[:50]}...")
                    
            else:
                print(f"   ❌ Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
        
        # Wait between requests
        if i < 2:
            print("   ⏳ Waiting 2 seconds...")
            time.sleep(2)
    
    print("\n" + "=" * 60)
    print("🎯 Expected Behavior:")
    print("   Request #1: External download (background upload to Telegram)")
    print("   Request #2: Fast cache response (<0.3s from Telegram)")
    print("   Request #3: Ultra-fast cache response (<0.3s from Telegram)")

if __name__ == "__main__":
    test_cache_performance()