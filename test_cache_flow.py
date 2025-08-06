#!/usr/bin/env python3
"""
Test script to verify Telegram cache-first flow is working properly
"""
import asyncio
import sys
import httpx
from services.api_service import api_service
from database.simple_mongo import init_db

async def test_cache_flow():
    """Test the complete cache flow"""
    print("🔍 Testing Cache-First Flow...")
    
    # Initialize database
    await init_db()
    
    # Test YouTube URL
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll for testing
    fake_api_key = "test_key_123"
    
    print(f"\n📱 Testing cache flow for: {test_url}")
    
    # Test 1: First request (should be cache miss and download)
    print("\n🔍 TEST 1: First request (expecting cache miss)")
    try:
        result1 = await api_service.process_youtube_request(
            fake_api_key, test_url, 'video', '360'
        )
        print(f"✅ First request result: {result1.get('source', 'unknown')}")
        if result1.get('cached'):
            print("⚡ Found in cache!")
        else:
            print("❌ Cache miss - will download and cache")
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
    
    print("\n" + "="*50)
    print("✅ Cache flow test completed!")
    print("Check the console output above to verify:")
    print("1. ✅ Cache checking happens FIRST")
    print("2. ✅ Background uploading starts after download")
    print("3. ✅ Proper console logging is working")

if __name__ == "__main__":
    asyncio.run(test_cache_flow())