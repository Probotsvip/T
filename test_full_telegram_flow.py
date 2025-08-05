#!/usr/bin/env python3
"""
Test Full Telegram Caching Flow
"""

import asyncio
import requests
from services.telegram_cache import TelegramCache
from database.simple_mongo import init_db

async def test_full_flow():
    """Test complete Telegram caching workflow"""
    
    print("🧪 Testing Full Telegram Caching Flow")
    print("=" * 50)
    
    # Initialize database
    await init_db()
    
    # Initialize Telegram cache
    cache = TelegramCache()
    
    print(f"📱 Telegram Available: {cache.telegram_available}")
    
    if not cache.telegram_available:
        print("❌ Telegram not available, testing fallback behavior")
        return
    
    # Test video info
    test_video_id = "dQw4w9WgXcQ"
    video_info = {
        'video_id': test_video_id,
        'title': 'Rick Astley - Never Gonna Give You Up (Official Video)',
        'duration': '3:33',
        'type': 'video',
        'quality': '360'
    }
    
    try:
        # 1. Check cache (should be empty first time)
        print("\n1. Checking cache (first time)...")
        cached = await cache.check_cache(test_video_id, 'video', '360')
        print(f"   Cache result: {cached is not None}")
        
        # 2. Test real API endpoint
        print("\n2. Testing real API endpoint...")
        response = requests.get(
            "http://localhost:5000/api/v1/video",
            params={
                "url": f"https://www.youtube.com/watch?v={test_video_id}",
                "quality": "360",
                "api_key": "demo-key"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API Success: {data.get('title', 'Unknown')}")
            print(f"   📺 Download URL: {data.get('download_url', 'Not available')[:50]}...")
            
            # 3. Test background caching (this happens automatically in the API)
            print("\n3. Background caching will happen automatically")
            print("   The API server caches content in the background")
            
        else:
            print(f"   ❌ API Failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Flow test failed: {e}")
    
    finally:
        await cache.close_session()

if __name__ == "__main__":
    asyncio.run(test_full_flow())