#!/usr/bin/env python3
"""
Fix Telegram bot configuration and test connection
"""
import os
import asyncio
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_telegram_bot_direct():
    """Test Telegram bot connection directly"""
    try:
        print("🤖 Testing Telegram Bot Connection...")
        
        # Import telegram library
        try:
            from telegram import Bot
            from telegram.error import TelegramError
            print("✅ Telegram library imported successfully")
        except ImportError as e:
            print(f"❌ Telegram library import failed: {e}")
            return False
        
        # Get configuration
        bot_token = "7412125068:AAE_xef9Tgq0MZXpknz3-WPPKK7hl6t3im0"
        channel_id = "-1002863131570"
        
        print(f"📱 Bot Token: {bot_token[:10]}...{bot_token[-10:]}")
        print(f"📺 Channel ID: {channel_id}")
        
        # Initialize bot
        print(f"🔄 Initializing bot...")
        bot = Bot(token=bot_token)
        
        # Test bot connection
        print(f"🔗 Testing bot connection...")
        try:
            bot_info = await bot.get_me()
            print(f"✅ Bot connected successfully!")
            print(f"   Bot name: {bot_info.first_name}")
            print(f"   Bot username: @{bot_info.username}")
            print(f"   Bot ID: {bot_info.id}")
        except TelegramError as e:
            print(f"❌ Bot connection failed: {e}")
            return False
        
        # Test channel access
        print(f"📢 Testing channel access...")
        try:
            chat_info = await bot.get_chat(channel_id)
            print(f"✅ Channel access successful!")
            print(f"   Channel title: {chat_info.title}")
            print(f"   Channel type: {chat_info.type}")
        except TelegramError as e:
            print(f"⚠️ Channel access limited: {e}")
            print(f"   This might be normal if bot doesn't have admin access")
        
        # Test simple message send
        print(f"📤 Testing message send...")
        try:
            test_message = "🚀 Telegram Cache Test - Bot is working correctly!"
            message = await bot.send_message(chat_id=channel_id, text=test_message)
            print(f"✅ Test message sent successfully!")
            print(f"   Message ID: {message.message_id}")
            
            # Clean up test message
            try:
                await bot.delete_message(chat_id=channel_id, message_id=message.message_id)
                print(f"🧹 Test message cleaned up")
            except:
                pass  # Don't worry if cleanup fails
                
        except TelegramError as e:
            print(f"❌ Message send failed: {e}")
            print(f"   Check if bot has proper permissions in the channel")
            return False
        
        print(f"\n🎉 Telegram bot is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Telegram bot test error: {e}")
        return False

async def fix_telegram_cache_class():
    """Fix the TelegramCache class initialization"""
    try:
        print(f"\n🔧 Testing TelegramCache class...")
        
        from services.telegram_cache import TelegramCache
        
        # Create instance
        telegram_cache = TelegramCache()
        
        print(f"📊 TelegramCache status:")
        print(f"   Available: {telegram_cache.telegram_available}")
        print(f"   Bot initialized: {telegram_cache.bot is not None}")
        print(f"   Channel configured: {telegram_cache.channel_id is not None}")
        
        if telegram_cache.telegram_available and telegram_cache.bot:
            # Test bot through cache class
            bot_info = await telegram_cache.bot.get_me()
            print(f"✅ TelegramCache working correctly!")
            print(f"   Bot: @{bot_info.username}")
            return True
        else:
            print(f"❌ TelegramCache not working")
            return False
            
    except Exception as e:
        print(f"❌ TelegramCache test error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Fixing Telegram Bot Configuration")
    print("=" * 50)
    
    # Test direct bot connection
    bot_success = asyncio.run(test_telegram_bot_direct())
    
    # Test through TelegramCache class
    cache_success = asyncio.run(fix_telegram_cache_class())
    
    print(f"\n" + "=" * 50)
    print(f"📊 Results:")
    print(f"   Direct Bot: {'✅' if bot_success else '❌'}")
    print(f"   Cache Class: {'✅' if cache_success else '❌'}")
    
    if bot_success and cache_success:
        print(f"\n🎉 TELEGRAM CACHE FIXED!")
        print(f"   Bot connection working")
        print(f"   Channel access configured")
        print(f"   Ready for video caching")
    else:
        print(f"\n⚠️ Telegram cache needs more attention")
        if not bot_success:
            print(f"   Fix bot token or permissions")
        if not cache_success:
            print(f"   Fix TelegramCache class initialization")