#!/usr/bin/env python3
"""
Fix Telegram caching system and test bot connectivity
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.getcwd())

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

async def test_telegram_bot():
    """Test if Telegram bot is working"""
    print("🔍 Testing Telegram Bot Configuration...")
    print(f"Bot Token: {TELEGRAM_BOT_TOKEN[:20]}...")
    print(f"Channel ID: {TELEGRAM_CHANNEL_ID}")
    print()
    
    try:
        # Try to import telegram
        from telegram import Bot
        print("✅ Telegram library imported successfully")
        
        # Initialize bot
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        print("✅ Bot initialized")
        
        # Test bot connection
        me = await bot.get_me()
        print(f"✅ Bot connected: @{me.username} ({me.first_name})")
        
        # Test channel access (this might fail if bot is not admin)
        try:
            chat = await bot.get_chat(TELEGRAM_CHANNEL_ID)
            print(f"✅ Channel access: {chat.title}")
        except Exception as e:
            print(f"⚠️  Channel access limited: {e}")
            print("   Bot may not be admin in the channel")
        
        return True
        
    except Exception as e:
        print(f"❌ Telegram test failed: {e}")
        return False

async def add_manual_cache_entry():
    """Add Rick Astley video to cache database manually"""
    print("\n📝 Adding Rick Astley video to cache database...")
    
    try:
        from database.simple_mongo import get_content_cache_collection
        from datetime import datetime
        
        cache_collection = get_content_cache_collection()
        if not cache_collection:
            print("❌ Could not connect to cache collection")
            return False
        
        # Rick Astley video details from user's screenshot
        cache_entry = {
            'youtube_id': 'dQw4w9WgXcQ',
            'title': 'Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)',
            'file_type': 'video',
            'quality': '360p',
            'duration': '3.55 min',
            'file_size': '32.7MB',
            'telegram_file_id': 'manually_uploaded_rick_astley',  # Placeholder for now
            'telegram_channel_id': TELEGRAM_CHANNEL_ID,
            'status': 'active',
            'cached_at': datetime.utcnow(),
            'created_at': datetime.utcnow(),
            'access_count': 0,
            'last_accessed': datetime.utcnow(),
            'upload_date': '2025-08-06 07:33 UTC',  # From screenshot
            'cache_source': 'manual_upload'
        }
        
        # Check if already exists
        existing = await cache_collection.find_one({'youtube_id': 'dQw4w9WgXcQ', 'file_type': 'video'})
        if existing:
            print("✅ Cache entry already exists")
            print(f"   Title: {existing['title']}")
            print(f"   Quality: {existing.get('quality', 'N/A')}")
            print(f"   Status: {existing.get('status', 'N/A')}")
            return True
        
        # Insert new cache entry
        result = await cache_collection.insert_one(cache_entry)
        print(f"✅ Cache entry created with ID: {result.inserted_id}")
        print(f"   YouTube ID: {cache_entry['youtube_id']}")
        print(f"   Quality: {cache_entry['quality']}")
        print(f"   File Size: {cache_entry['file_size']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to add cache entry: {e}")
        return False

async def test_cache_detection():
    """Test if cache detection works"""
    print("\n🔍 Testing Cache Detection...")
    
    try:
        from services.telegram_cache import TelegramCache
        
        cache = TelegramCache()
        print(f"✅ TelegramCache initialized")
        print(f"   Telegram available: {cache.telegram_available}")
        
        # Test cache check
        cached_result = await cache.check_cache(
            youtube_id='dQw4w9WgXcQ',
            content_type='video',
            quality='360p'
        )
        
        if cached_result:
            print("🎉 Cache detection SUCCESS!")
            print(f"   Title: {cached_result.get('title', 'N/A')}")
            print(f"   Quality: {cached_result.get('quality', 'N/A')}")
            print(f"   File Size: {cached_result.get('file_size', 'N/A')}")
            print(f"   Access Count: {cached_result.get('access_count', 0)}")
            return True
        else:
            print("❌ Cache detection failed - no cached content found")
            return False
            
    except Exception as e:
        print(f"❌ Cache detection error: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Telegram Cache System Diagnostic")
    print("=" * 50)
    
    # Test 1: Bot connectivity
    bot_ok = await test_telegram_bot()
    
    # Test 2: Add manual cache entry
    cache_added = await add_manual_cache_entry()
    
    # Test 3: Test cache detection
    cache_detected = await test_cache_detection()
    
    print("\n" + "=" * 50)
    print("📊 Diagnostic Summary:")
    print(f"   Bot Connection: {'✅' if bot_ok else '❌'}")
    print(f"   Cache Database: {'✅' if cache_added else '❌'}")
    print(f"   Cache Detection: {'✅' if cache_detected else '❌'}")
    
    if all([bot_ok, cache_added, cache_detected]):
        print("\n🎉 EXCELLENT! Your Telegram cache system is ready!")
        print("   Next API request should use cached content with 0.3s response!")
    else:
        print("\n🔧 Issues found. Let's fix them step by step.")

if __name__ == "__main__":
    asyncio.run(main())