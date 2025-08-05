#!/usr/bin/env python3
import asyncio
import io
import httpx
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID

async def download_and_upload():
    """Manual test of complete background process"""
    try:
        print("🔄 Testing complete background process...")
        
        # 1. Download the video
        url = "https://cdn400.savetube.su/media/DoaE_6Y2_8I/morni-official-music-video-darshan-raval-divyansha-k-siddharth-a-b-naushad-khan-indie-music-360-ytshorts.savetube.me.mp4"
        
        print("📥 Downloading video file...")
        session = httpx.AsyncClient(timeout=300.0)
        
        file_content = io.BytesIO()
        total_size = 0
        
        async with session.stream('GET', url) as response:
            if response.status_code != 200:
                print(f"❌ Download failed: {response.status_code}")
                return False
                
            print(f"✅ Download started, status: {response.status_code}")
            
            async for chunk in response.aiter_bytes(chunk_size=8192):
                file_content.write(chunk)
                total_size += len(chunk)
                
                # Small limit for testing
                if total_size > 5 * 1024 * 1024:  # 5MB limit
                    print(f"📊 Downloaded {total_size/1024/1024:.1f}MB - stopping for test")
                    break
        
        await session.aclose()
        file_content.seek(0)
        
        print(f"📤 Uploading {total_size/1024/1024:.1f}MB to Telegram...")
        
        # 2. Upload to Telegram
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        message = await bot.send_video(
            chat_id=TELEGRAM_CHANNEL_ID,
            video=file_content,
            filename="Morni_Official_Music_Video_360p.mp4",
            caption="🎬 Morni Official Music Video | Darshan Raval\nVideo ID: DoaE_6Y2_8I\nQuality: 360p\n\n📱 Cached by YouTube API Server",
            supports_streaming=True
        )
        
        print(f"✅ Successfully uploaded to Telegram!")
        print(f"📋 File ID: {message.video.file_id}")
        print(f"📂 File size: {message.video.file_size} bytes")
        
        return message.video.file_id
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(download_and_upload())
    print(f"\n🎯 Final result: {'Success' if result else 'Failed'}")
    if result:
        print(f"Telegram File ID: {result}")