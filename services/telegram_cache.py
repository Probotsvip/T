import asyncio
import io
from datetime import datetime
from typing import Optional, Dict, Any, BinaryIO
import httpx
from telegram import Bot
from telegram.error import TelegramError
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
from database.mongo import get_content_cache_collection
from models import ContentCache
from utils.logging import LOGGER

logger = LOGGER(__name__)

class TelegramCache:
    def __init__(self):
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        self.channel_id = TELEGRAM_CHANNEL_ID
        self.session = None
        
    async def get_session(self):
        """Get HTTP session for file downloads"""
        if not self.session:
            self.session = httpx.AsyncClient(
                timeout=300.0,  # 5 minutes for large files
                limits=httpx.Limits(max_keepalive_connections=50, max_connections=500)
            )
        return self.session
    
    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.aclose()
            self.session = None
    
    async def check_cache(self, youtube_id: str, content_type: str, quality: str = None) -> Optional[Dict[str, Any]]:
        """Check if content exists in Telegram cache"""
        try:
            cache_collection = get_content_cache_collection()
            
            query = {
                'youtube_id': youtube_id,
                'file_type': content_type
            }
            
            if quality and content_type == 'video':
                query['quality'] = quality
            
            cached_content = await cache_collection.find_one(query)
            
            if cached_content:
                # Update access stats
                await cache_collection.update_one(
                    {'_id': cached_content['_id']},
                    {
                        '$inc': {'access_count': 1},
                        '$set': {'last_accessed': datetime.utcnow()}
                    }
                )
                
                logger.info(f"Cache hit for {youtube_id} ({content_type})")
                return {
                    'telegram_file_id': cached_content['telegram_file_id'],
                    'title': cached_content['title'],
                    'duration': cached_content['duration'],
                    'file_type': cached_content['file_type'],
                    'quality': cached_content.get('quality'),
                    'cached': True
                }
            
            logger.info(f"Cache miss for {youtube_id} ({content_type})")
            return None
            
        except Exception as e:
            logger.error(f"Cache check failed: {e}")
            return None
    
    async def download_and_cache(self, download_url: str, video_info: Dict[str, Any]) -> Optional[str]:
        """Download content and upload to Telegram for caching"""
        try:
            session = await self.get_session()
            
            logger.info(f"Downloading content from: {download_url}")
            
            # Stream download to avoid memory issues
            async with session.stream('GET', download_url) as response:
                if response.status_code != 200:
                    raise Exception(f"Download failed with status {response.status_code}")
                
                # Create in-memory file
                file_content = io.BytesIO()
                total_size = 0
                
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    file_content.write(chunk)
                    total_size += len(chunk)
                    
                    # Limit file size (50MB for Telegram)
                    if total_size > 50 * 1024 * 1024:
                        raise Exception("File too large for Telegram (>50MB)")
                
                file_content.seek(0)
                
                # Determine file extension
                content_type = video_info.get('type', 'video')
                quality = video_info.get('quality', '360')
                extension = 'mp3' if content_type == 'audio' else 'mp4'
                filename = f"{video_info['title'][:50]}.{extension}"
                
                # Upload to Telegram
                logger.info(f"Uploading to Telegram: {filename}")
                
                if content_type == 'audio':
                    message = await self.bot.send_audio(
                        chat_id=self.channel_id,
                        audio=file_content,
                        title=video_info['title'],
                        duration=self.parse_duration(video_info.get('duration', '0:00')),
                        filename=filename
                    )
                    telegram_file_id = message.audio.file_id
                else:
                    message = await self.bot.send_video(
                        chat_id=self.channel_id,
                        video=file_content,
                        caption=f"{video_info['title']}\nQuality: {quality}p",
                        filename=filename
                    )
                    telegram_file_id = message.video.file_id
                
                # Save to cache database
                cache_entry = ContentCache(
                    youtube_id=video_info['video_id'],
                    title=video_info['title'],
                    duration=video_info['duration'],
                    telegram_file_id=telegram_file_id,
                    file_type=content_type,
                    quality=quality if content_type == 'video' else None
                )
                
                cache_collection = get_content_cache_collection()
                await cache_collection.insert_one(cache_entry.to_dict())
                
                logger.info(f"Successfully cached content: {telegram_file_id}")
                return telegram_file_id
                
        except TelegramError as e:
            logger.error(f"Telegram upload failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Download and cache failed: {e}")
            return None
    
    async def get_file_stream_url(self, telegram_file_id: str) -> Optional[str]:
        """Get streaming URL from Telegram file"""
        try:
            file = await self.bot.get_file(telegram_file_id)
            return file.file_path
        except TelegramError as e:
            logger.error(f"Failed to get file stream URL: {e}")
            return None
    
    async def stream_file_content(self, telegram_file_id: str) -> Optional[BinaryIO]:
        """Stream file content directly from Telegram"""
        try:
            file_url = await self.get_file_stream_url(telegram_file_id)
            if not file_url:
                return None
            
            session = await self.get_session()
            response = await session.get(file_url)
            
            if response.status_code == 200:
                return io.BytesIO(response.content)
            
            return None
            
        except Exception as e:
            logger.error(f"File streaming failed: {e}")
            return None
    
    def parse_duration(self, duration_str: str) -> int:
        """Parse duration string to seconds"""
        try:
            parts = duration_str.split(':')
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            return 0
        except:
            return 0
    
    async def cleanup_old_cache(self, days: int = 30):
        """Clean up old cached content"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            cache_collection = get_content_cache_collection()
            old_entries = cache_collection.find({
                'created_at': {'$lt': cutoff_date},
                'access_count': {'$lt': 10}  # Remove rarely accessed content
            })
            
            deleted_count = 0
            async for entry in old_entries:
                try:
                    # Note: We can't delete files from Telegram channel easily
                    # So we just remove the database entry
                    await cache_collection.delete_one({'_id': entry['_id']})
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete cache entry {entry['_id']}: {e}")
            
            logger.info(f"Cleaned up {deleted_count} old cache entries")
            
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")

# Global cache instance
telegram_cache = TelegramCache()
