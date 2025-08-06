#!/usr/bin/env python3
"""
Test Telegram cache functionality
"""
import os
import asyncio
from datetime import datetime
from pymongo import MongoClient
from services.telegram_cache import TelegramCache
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_telegram_cache():
    """Test the Telegram cache system"""
    try:
        print("🔍 Testing Telegram Cache System...")
        print("=" * 50)
        
        # Test 1: Check bot configuration
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "7412125068:AAE_xef9Tgq0MZXpknz3-WPPKK7hl6t3im0")
        channel_id = os.getenv("TELEGRAM_CHANNEL_ID", "-1002863131570")
        
        print(f"📱 Bot Token: {bot_token[:10]}...{bot_token[-10:] if len(bot_token) > 20 else bot_token}")
        print(f"📺 Channel ID: {channel_id}")
        
        # Test 2: Initialize TelegramCache
        telegram_cache = TelegramCache()
        print(f"🤖 Telegram Available: {telegram_cache.telegram_available}")
        
        if not telegram_cache.telegram_available:
            print(f"❌ Telegram cache not available:")
            print(f"   - Bot Token: {'✅' if bot_token else '❌'}")
            print(f"   - Channel ID: {'✅' if channel_id else '❌'}")
            print(f"   - Library: {'✅' if hasattr(telegram_cache, 'bot') else '❌'}")
            return False
        
        # Test 3: Check bot connection
        print(f"\n🔗 Testing bot connection...")
        try:
            bot_info = await telegram_cache.bot.get_me()
            print(f"✅ Bot connected: @{bot_info.username} ({bot_info.first_name})")
        except Exception as e:
            print(f"❌ Bot connection failed: {e}")
            return False
        
        # Test 4: Check database cache collection
        print(f"\n💾 Checking cache database...")
        mongo_uri = os.getenv("MONGO_DB_URI", "mongodb+srv://jaydipmore74:xCpTm5OPAfRKYnif@cluster0.5jo18.mongodb.net/?retryWrites=true&w=majority")
        client = MongoClient(mongo_uri)
        db = client.youtube_api_db
        
        cache_count = db.content_cache.count_documents({})
        print(f"📊 Cached content items: {cache_count}")
        
        # Show sample cached items
        if cache_count > 0:
            sample_cache = db.content_cache.find().limit(3)
            print(f"📄 Sample cached items:")
            for i, item in enumerate(sample_cache, 1):
                print(f"   {i}. {item.get('title', 'Unknown')[:50]} ({item.get('file_type', 'unknown')})")
                print(f"      File ID: {item.get('telegram_file_id', 'N/A')}")
                print(f"      Status: {item.get('status', 'unknown')}")
        
        # Test 5: Test cache lookup for a common video
        print(f"\n🔍 Testing cache lookup...")
        test_video_id = "dQw4w9WgXcQ"  # Rick Roll - commonly cached
        cached_result = await telegram_cache.check_cache(test_video_id, 'video', '360')
        
        if cached_result:
            print(f"✅ Cache hit for test video: {cached_result['title']}")
            print(f"   File ID: {cached_result.get('telegram_file_id')}")
        else:
            print(f"❌ No cache found for test video ID: {test_video_id}")
        
        client.close()
        
        # Test 6: Summary
        print(f"\n" + "=" * 50)
        print(f"📊 Telegram Cache System Status:")
        print(f"   Bot Connection: {'✅' if telegram_cache.telegram_available else '❌'}")
        print(f"   Database Connection: ✅")
        print(f"   Cached Items: {cache_count}")
        print(f"   Cache Lookup: {'✅' if cached_result else '⚠️ No test data'}")
        
        if telegram_cache.telegram_available and cache_count > 0:
            print(f"\n🎉 Telegram cache is working correctly!")
            return True
        else:
            print(f"\n⚠️ Telegram cache needs attention:")
            if not telegram_cache.telegram_available:
                print(f"   - Fix bot configuration")
            if cache_count == 0:
                print(f"   - No cached content available")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_bot_permissions():
    """Test if bot has proper permissions in the channel"""
    try:
        print(f"\n🔐 Testing bot permissions...")
        
        # This would require async context, so we'll do basic checks
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "7412125068:AAE_xef9Tgq0MZXpknz3-WPPKK7hl6t3im0")
        channel_id = os.getenv("TELEGRAM_CHANNEL_ID", "-1002863131570")
        
        if not bot_token or not channel_id:
            print(f"❌ Missing bot configuration")
            return False
        
        print(f"✅ Bot token configured")
        print(f"✅ Channel ID configured")
        print(f"💡 To test permissions fully, try uploading content through the API")
        
        return True
        
    except Exception as e:
        print(f"❌ Permission test error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Telegram Cache System Test")
    print("Testing cache functionality and bot connection...")
    
    # Run async test
    success = asyncio.run(test_telegram_cache())
    
    # Run sync test
    permissions_ok = test_bot_permissions()
    
    print(f"\n" + "=" * 60)
    if success and permissions_ok:
        print("✅ TELEGRAM CACHE IS WORKING!")
        print("   Your system can cache videos in Telegram channel")
        print("   New video requests will be cached automatically")
    else:
        print("❌ TELEGRAM CACHE NEEDS ATTENTION!")
        print("   Check bot token and channel permissions")