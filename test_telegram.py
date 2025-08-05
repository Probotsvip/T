#!/usr/bin/env python3
"""
Test Telegram Integration
"""

import asyncio
from services.telegram_cache import TelegramCache
from utils.logging import LOGGER

logger = LOGGER(__name__)

async def test_telegram():
    """Test Telegram bot integration"""
    
    print("🧪 Testing Telegram Integration")
    print("=" * 40)
    
    try:
        # Initialize cache
        cache = TelegramCache()
        
        print(f"📱 Telegram Available: {cache.telegram_available}")
        print(f"🤖 Bot: {cache.bot is not None}")
        print(f"📢 Channel ID: {cache.channel_id}")
        
        if cache.telegram_available:
            print("✅ Telegram integration is working")
            
            # Test cache check
            test_video_id = "dQw4w9WgXcQ"
            cache_result = await cache.check_cache(test_video_id, "video", "360")
            print(f"📦 Cache check result: {cache_result is not None}")
            
        else:
            print("❌ Telegram integration not available")
            print("   Reasons could be:")
            print("   • Bot token missing or invalid")
            print("   • Channel ID missing or invalid")
            print("   • python-telegram-bot package issues")
            
        await cache.close_session()
        
    except Exception as e:
        print(f"❌ Telegram test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_telegram())