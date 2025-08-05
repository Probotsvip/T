#!/usr/bin/env python3
import asyncio
import io
import httpx
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

async def test_telegram_upload():
    """Test direct Telegram upload"""
    try:
        print("🔄 Testing Telegram upload...")
        
        # Test with small dummy file
        file_content = io.BytesIO(b"Test video content for YouTube API Server")
        file_content.seek(0)
        
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        message = await bot.send_document(
            chat_id=TELEGRAM_CHANNEL_ID,
            document=file_content,
            filename="test_upload.txt",
            caption="🎬 Test upload from YouTube API Server\nVideo ID: test123"
        )
        
        print(f"✅ Successfully uploaded to Telegram! File ID: {message.document.file_id}")
        return True
        
    except Exception as e:
        print(f"❌ Telegram upload error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_telegram_upload())
    print(f"Test result: {'Success' if result else 'Failed'}")