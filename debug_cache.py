#!/usr/bin/env python3
"""
Debug cache issue - check why background uploading isn't working
"""
import asyncio
import sys
from services.telegram_cache import TelegramCache
from services.api_service import api_service
from database.simple_mongo import init_db

async def debug_cache_system():
    """Debug the cache system step by step"""
    print("🔍 Debugging Cache System...")
    
    # Initialize database
    await init_db()
    
    # Test URL that we know exists in cache
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll
    video_id = "dQw4w9WgXcQ"
    
    print(f"\n📱 Testing video: {video_id}")
    
    # Test 1: Check Telegram cache directly
    print("\n🔍 TEST 1: Direct Telegram cache check")
    telegram_cache = TelegramCache()
    print(f"Telegram available: {telegram_cache.telegram_available}")
    print(f"Bot token exists: {bool(telegram_cache.bot)}")
    print(f"Channel ID: {telegram_cache.channel_id}")
    
    if telegram_cache.telegram_available:
        cached_result = await telegram_cache.check_cache(video_id, 'video', '360')
        if cached_result:
            print(f"✅ Found in Telegram: {cached_result.get('title', 'Unknown')}")
        else:
            print("❌ Not found in Telegram cache")
    else:
        print("❌ Telegram not available")
    
    # Test 2: Check background upload functionality 
    print("\n🔍 TEST 2: Background upload test")
    fake_download_result = {
        'status': True,
        'video_id': 'test_video_123',
        'title': 'Test Video for Upload',
        'duration': '3:45',
        'download_url': 'https://example.com/test.mp4',
        'source_url': 'https://youtube.com/watch?v=test_video_123',
        'thumbnail': 'https://example.com/thumb.jpg',
        'uploader': 'Test Channel'
    }
    
    try:
        # Try background caching
        await api_service._cache_content_background(fake_download_result, 'video', '360')
        print("✅ Background cache function works")
    except Exception as e:
        print(f"❌ Background cache failed: {e}")
    
    # Test 3: Check video ID extraction
    print("\n🔍 TEST 3: Video ID extraction")
    from services.youtube_downloader import extract_video_id
    extracted_id = extract_video_id(test_url)
    print(f"Extracted ID: {extracted_id}")
    
    print("\n" + "="*50)
    print("🔍 Debug Summary:")
    print("1. Check if Telegram credentials are working")
    print("2. Check if background upload function runs without errors")
    print("3. Check if video ID extraction is correct")

if __name__ == "__main__":
    asyncio.run(debug_cache_system())