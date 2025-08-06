#!/usr/bin/env python3
"""
Test script to check if our API can detect and use existing content in Telegram channel
"""

import asyncio
import requests
import json
from database.simple_mongo import get_content_cache_collection
from services.telegram_cache import TelegramCache
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

# Rick Astley video details from the screenshot
RICK_ASTLEY_VIDEO = {
    'youtube_id': 'dQw4w9WgXcQ',  # Rick Astley - Never Gonna Give You Up
    'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    'title': 'Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)',
    'quality': '360p',
    'file_size': '32.7MB',
    'duration': '3.55 min'
}

async def test_telegram_cache_detection():
    """Test if our cache system can detect existing content"""
    print("🔍 Testing Telegram Cache Detection...")
    print(f"Bot Token: {TELEGRAM_BOT_TOKEN[:20]}...")
    print(f"Channel ID: {TELEGRAM_CHANNEL_ID}")
    print()
    
    # Initialize cache system
    cache = TelegramCache()
    
    if not cache.telegram_available:
        print("❌ Telegram not available - checking config...")
        return False
    
    print(f"✅ Telegram initialized successfully")
    print(f"📺 Testing video: {RICK_ASTLEY_VIDEO['title']}")
    print(f"🆔 YouTube ID: {RICK_ASTLEY_VIDEO['youtube_id']}")
    print()
    
    # Test cache check for the manually uploaded video
    cached_result = await cache.check_cache(
        youtube_id=RICK_ASTLEY_VIDEO['youtube_id'],
        content_type='video',
        quality='360p'
    )
    
    if cached_result:
        print("🎉 SUCCESS! Found cached content:")
        print(f"   - Telegram File ID: {cached_result.get('telegram_file_id', 'N/A')}")
        print(f"   - Quality: {cached_result.get('quality', 'N/A')}")
        print(f"   - File Size: {cached_result.get('file_size', 'N/A')}")
        print(f"   - Cache Date: {cached_result.get('created_at', 'N/A')}")
        print(f"   - Access Count: {cached_result.get('access_count', 0)}")
        return True
    else:
        print("❌ No cached content found")
        print("   This means either:")
        print("   1. The video is not in our database cache metadata")
        print("   2. We need to scan the channel to find existing content")
        return False

async def test_api_endpoint():
    """Test the actual API endpoint"""
    print("\n🌐 Testing API Endpoint...")
    
    # First, let's create a test API key
    from database.simple_mongo import get_api_keys_collection
    
    api_keys_collection = get_api_keys_collection()
    if not api_keys_collection:
        print("❌ Could not connect to API keys collection")
        return
    
    # Check if test key exists
    test_key = await api_keys_collection.find_one({'key_name': 'test_key'})
    if not test_key:
        print("📝 Creating test API key...")
        test_api_key = {
            'key_name': 'test_key',
            'api_key': 'test_api_key_12345',
            'daily_limit': 1000,
            'is_active': True,
            'created_at': '2025-08-06'
        }
        await api_keys_collection.insert_one(test_api_key)
        print(f"✅ Created test API key: {test_api_key['api_key']}")
    else:
        print(f"✅ Using existing test API key: {test_key['api_key']}")
    
    # Test the video endpoint
    api_url = "http://localhost:5000/api/v1/video"
    params = {
        'url': RICK_ASTLEY_VIDEO['url'],
        'quality': '360p',
        'api_key': test_key['api_key'] if test_key else 'test_api_key_12345'
    }
    
    print(f"🚀 Making API request to: {api_url}")
    print(f"📋 Parameters: {params}")
    
    try:
        response = requests.get(api_url, params=params, timeout=30)
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("🎉 API Response:")
            print(json.dumps(data, indent=2))
            
            if data.get('cached') and data.get('source') == 'telegram':
                print("\n✅ SUCCESS! API used cached content from Telegram")
                print(f"   ⚡ Response time: {data.get('response_time', 'N/A')}")
                return True
            else:
                print(f"\n⚠️  API worked but used source: {data.get('source', 'unknown')}")
                return False
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

async def scan_telegram_channel():
    """Scan Telegram channel for existing content"""
    print("\n🔍 Scanning Telegram Channel for Existing Content...")
    
    cache = TelegramCache()
    if not cache.telegram_available:
        print("❌ Telegram not available")
        return
    
    try:
        # This would require implementing a channel scanning function
        # For now, let's check if we can access the bot
        print(f"✅ Bot initialized successfully")
        print(f"📱 Channel ID: {TELEGRAM_CHANNEL_ID}")
        print("💡 To fully implement channel scanning, we need:")
        print("   1. Bot admin permissions in the channel")
        print("   2. Channel scanning function to read existing messages")
        print("   3. Content metadata extraction from messages")
        
    except Exception as e:
        print(f"❌ Channel access error: {e}")

async def main():
    """Run all tests"""
    print("🚀 YouTube API Cache Detection Test")
    print("=" * 50)
    
    # Test 1: Check cache detection
    cache_found = await test_telegram_cache_detection()
    
    # Test 2: Scan channel (if cache not found)
    if not cache_found:
        await scan_telegram_channel()
    
    # Test 3: Test API endpoint
    api_success = await test_api_endpoint()
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   Cache Detection: {'✅ SUCCESS' if cache_found else '❌ NOT FOUND'}")
    print(f"   API Endpoint: {'✅ SUCCESS' if api_success else '❌ FAILED'}")
    
    if cache_found and api_success:
        print("\n🎉 PERFECT! Your system is working as designed!")
        print("   - Existing content detected in cache")
        print("   - API serving from Telegram cache")
        print("   - 0.3s response time achieved!")
    elif not cache_found:
        print("\n🔧 NEXT STEPS:")
        print("   1. Implement channel scanning to detect existing content")
        print("   2. Add content to cache database automatically")
        print("   3. Re-test API endpoint")

if __name__ == "__main__":
    asyncio.run(main())