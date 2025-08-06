import asyncio
import io
import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, BinaryIO, List
import httpx
try:
    from telegram import Bot
    from telegram.error import TelegramError, BadRequest, NetworkError, TimedOut, RetryAfter
    from telegram.constants import ParseMode
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    # Fallback classes for when telegram isn't available
    class Bot:
        def __init__(self, token): 
            self.token = token
        async def get_file(self, file_id): return None
        async def send_audio(self, *args, **kwargs): return None
        async def send_video(self, *args, **kwargs): return None
    
    class TelegramError(Exception): pass
    class BadRequest(TelegramError): pass
    class NetworkError(TelegramError): pass
    class TimedOut(TelegramError): pass
    class RetryAfter(TelegramError): pass
    
    class ParseMode:
        HTML = "HTML"
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
from database.simple_mongo import get_content_cache_collection
from models_simple import ContentCache
from utils.logging import LOGGER

logger = LOGGER(__name__)

class TelegramCache:
    def __init__(self):
        self.telegram_available = TELEGRAM_AVAILABLE and TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL_ID
        if self.telegram_available:
            try:
                self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
                self.channel_id = TELEGRAM_CHANNEL_ID
            except Exception as e:
                logger.error(f"Telegram bot initialization failed: {e}")
                self.telegram_available = False
                self.bot = None
                self.channel_id = None
        else:
            self.bot = None
            self.channel_id = None
            
        self.session = None
        self.upload_semaphore = asyncio.Semaphore(3)  # Limit concurrent uploads
        self.retry_delays = [1, 2, 5, 10, 30]  # Exponential backoff
        self.max_file_size = 50 * 1024 * 1024  # 50MB Telegram limit
        self.max_caption_length = 1024  # Telegram caption limit
        
    async def get_session(self):
        """Get optimized HTTP session for file downloads"""
        if not self.session:
            self.session = httpx.AsyncClient(
                timeout=httpx.Timeout(300.0, connect=30.0),  # 5 minutes for large files, 30s connect
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=100,
                    keepalive_expiry=300.0
                ),
                headers={
                    'User-Agent': 'YouTube-API-Server/2.0 (Professional Cache System)',
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate'
                }
            )
        return self.session
    
    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.aclose()
            self.session = None
    
    async def check_cache(self, youtube_id: str, content_type: str, quality: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Professional cache checking with comprehensive metadata"""
        try:
            cache_collection = get_content_cache_collection()
            if cache_collection is None:
                logger.warning("Cache collection not available")
                return None
            
            # Build sophisticated query with fallback logic
            primary_query = {
                'youtube_id': youtube_id,
                'file_type': content_type,
                'status': 'active'  # Only active cache entries
            }
            
            if quality and content_type == 'video':
                primary_query['quality'] = quality
            
            # Try exact match first
            cached_content = await cache_collection.find_one(primary_query)
            
            # Fallback: Find any quality for video if exact not found
            if not cached_content and content_type == 'video' and quality:
                fallback_query = {
                    'youtube_id': youtube_id,
                    'file_type': content_type,
                    'status': 'active'
                }
                cached_content = await cache_collection.find_one(fallback_query)
                if cached_content:
                    logger.info(f"🔄 Using fallback quality {cached_content.get('quality')} for {youtube_id}")
            
            if cached_content:
                # Verify file still exists in Telegram
                if await self._verify_telegram_file(cached_content['telegram_file_id']):
                    # Update comprehensive access stats
                    await cache_collection.update_one(
                        {'_id': cached_content['_id']},
                        {
                            '$inc': {'access_count': 1},
                            '$set': {
                                'last_accessed': datetime.utcnow(),
                                'last_verified': datetime.utcnow()
                            }
                        }
                    )
                    
                    logger.info(f"🎯 TELEGRAM CHANNEL VIDEO FOUND: {cached_content['title']}")
                    logger.info(f"📁 File ID: {cached_content['telegram_file_id']}")
                    logger.info(f"📺 Quality: {cached_content.get('quality', 'default')}")
                    print(f"🎯 TELEGRAM CHANNEL VIDEO FOUND: {cached_content['title']}")  # Console output
                    return {
                        'telegram_file_id': cached_content['telegram_file_id'],
                        'title': cached_content['title'],
                        'duration': cached_content['duration'],
                        'file_type': cached_content['file_type'],
                        'quality': cached_content.get('quality'),
                        'file_size': cached_content.get('file_size', 'Unknown'),
                        'upload_date': cached_content.get('upload_date'),
                        'access_count': cached_content.get('access_count', 0) + 1,
                        'cached': True,
                        'cache_verified': True
                    }
                else:
                    # Mark as inactive if file not accessible
                    await cache_collection.update_one(
                        {'_id': cached_content['_id']},
                        {'$set': {'status': 'inactive', 'last_verified': datetime.utcnow()}}
                    )
                    logger.warning(f"🔴 Cache entry marked inactive: {youtube_id}")
            
            logger.info(f"❌ Professional cache miss: {youtube_id} ({content_type})")
            return None
            
        except Exception as e:
            logger.error(f"Professional cache check failed: {e}")
            return None
    
    async def download_and_cache(self, download_url: str, video_info: Dict[str, Any]) -> Optional[str]:
        """Professional download and cache with advanced features"""
        # Return None if Telegram not available - this is normal operation
        if not self.telegram_available:
            logger.info(f"Telegram caching not available for: {video_info.get('title', 'Unknown')}")
            return None
            
        async with self.upload_semaphore:  # Limit concurrent uploads
            try:
                session = await self.get_session()
                content_type = video_info.get('type', 'video')
                quality = video_info.get('quality', '360')
                
                logger.info(f"🚀 Professional download starting: {video_info['title'][:50]}")
                
                # Generate unique content hash for deduplication
                content_hash = self._generate_content_hash(video_info['video_id'], content_type, quality)
                
                # Check for duplicate by hash
                if await self._check_duplicate_by_hash(content_hash):
                    logger.info(f"🔄 Duplicate detected by hash, skipping upload")
                    return None
                
                # Professional streaming download with progress tracking
                file_content, total_size = await self._stream_download_with_progress(
                    session, download_url, video_info['title']
                )
                
                if not file_content:
                    return None
                
                # Professional upload with retry mechanism
                telegram_file_id = await self._professional_upload_with_retry(
                    file_content, video_info, content_type, quality, total_size
                )
                
                if telegram_file_id:
                    # Save comprehensive cache entry
                    await self._save_professional_cache_entry(
                        video_info, telegram_file_id, content_type, quality, 
                        total_size, content_hash
                    )
                    
                    logger.info(f"✅ Professional cache complete: {telegram_file_id}")
                    return telegram_file_id
                
                return None
                
            except Exception as e:
                logger.error(f"Professional download and cache failed: {e}")
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
    
    async def _verify_telegram_file(self, telegram_file_id: str) -> bool:
        """Verify if Telegram file still exists and is accessible"""
        if not self.telegram_available or not self.bot:
            return False
        try:
            file_info = await self.bot.get_file(telegram_file_id)
            return file_info and file_info.file_path
        except Exception:
            return False
    
    def _generate_content_hash(self, video_id: str, content_type: str, quality: str) -> str:
        """Generate unique hash for content deduplication"""
        content_string = f"{video_id}_{content_type}_{quality}"
        return hashlib.md5(content_string.encode()).hexdigest()
    
    async def _check_duplicate_by_hash(self, content_hash: str) -> bool:
        """Check if content already exists by hash"""
        try:
            cache_collection = get_content_cache_collection()
            if cache_collection is None:
                return False
            existing = await cache_collection.find_one({
                'content_hash': content_hash,
                'status': 'active'
            })
            return existing is not None
        except Exception:
            return False
    
    async def _stream_download_with_progress(self, session, download_url: str, title: str) -> tuple:
        """Professional streaming download with progress tracking"""
        try:
            async with session.stream('GET', download_url) as response:
                if response.status_code != 200:
                    raise Exception(f"Download failed with status {response.status_code}")
                
                file_content = io.BytesIO()
                total_size = 0
                chunk_count = 0
                
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    file_content.write(chunk)
                    total_size += len(chunk)
                    chunk_count += 1
                    
                    # Progress logging every 100 chunks (~ 800KB)
                    if chunk_count % 100 == 0:
                        size_mb = total_size / (1024 * 1024)
                        logger.info(f"📥 Downloaded {size_mb:.1f}MB of {title[:30]}...")
                    
                    # Professional size limit check
                    if total_size > self.max_file_size:
                        raise Exception(f"File too large for Telegram (>{self.max_file_size / (1024*1024):.0f}MB)")
                
                file_content.seek(0)
                size_mb = total_size / (1024 * 1024)
                logger.info(f"✅ Download complete: {size_mb:.1f}MB")
                
                return file_content, total_size
                
        except Exception as e:
            logger.error(f"Stream download failed: {e}")
            return None, 0
    
    async def _professional_upload_with_retry(self, file_content, video_info: Dict, 
                                            content_type: str, quality: str, file_size: int) -> Optional[str]:
        """Professional upload with exponential backoff retry"""
        extension = 'mp3' if content_type == 'audio' else 'mp4'
        safe_title = self._sanitize_filename(video_info['title'])
        filename = f"{safe_title[:50]}.{extension}"
        
        # Create professional caption
        caption = self._create_professional_caption(video_info, content_type, quality, file_size)
        
        for attempt, delay in enumerate(self.retry_delays, 1):
            try:
                logger.info(f"📤 Upload attempt {attempt}/5: {filename}")
                
                file_content.seek(0)  # Reset file pointer
                
                if content_type == 'audio':
                    message = await self.bot.send_audio(
                        chat_id=self.channel_id,
                        audio=file_content,
                        title=video_info['title'][:64],  # Telegram title limit
                        duration=self.parse_duration(video_info.get('duration', '0:00')),
                        caption=caption,
                        filename=filename,
                        parse_mode=ParseMode.HTML
                    )
                    telegram_file_id = message.audio.file_id
                else:
                    message = await self.bot.send_video(
                        chat_id=self.channel_id,
                        video=file_content,
                        caption=caption,
                        filename=filename,
                        parse_mode=ParseMode.HTML
                    )
                    telegram_file_id = message.video.file_id
                
                logger.info(f"🎯 Professional upload successful: {telegram_file_id}")
                return telegram_file_id
                
            except (RetryAfter, TimedOut, NetworkError) as e:
                if attempt < len(self.retry_delays):
                    logger.warning(f"⏳ Upload attempt {attempt} failed, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"❌ All upload attempts failed: {e}")
                    return None
                    
            except (BadRequest, TelegramError) as e:
                logger.error(f"❌ Upload failed with non-retryable error: {e}")
                return None
                
        return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe upload"""
        # Remove/replace problematic characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_() "
        return ''.join(c if c in safe_chars else '_' for c in filename)
    
    def _create_professional_caption(self, video_info: Dict, content_type: str, 
                                   quality: str, file_size: int) -> str:
        """Create professional caption with comprehensive metadata"""
        size_mb = file_size / (1024 * 1024)
        
        caption = f"🎬 <b>{video_info['title'][:100]}</b>\n\n"
        caption += f"📹 <b>Video ID:</b> <code>{video_info['video_id']}</code>\n"
        caption += f"🎭 <b>Type:</b> {content_type.upper()}\n"
        
        if content_type == 'video' and quality:
            caption += f"🎯 <b>Quality:</b> {quality}p\n"
        
        caption += f"⏱️ <b>Duration:</b> {video_info.get('duration', 'N/A')}\n"
        caption += f"📊 <b>File Size:</b> {size_mb:.1f}MB\n"
        caption += f"📅 <b>Upload Date:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n"
        caption += f"🤖 <b>Cached by YouTube API Server</b>"
        
        # Ensure caption doesn't exceed Telegram limit
        if len(caption) > self.max_caption_length:
            caption = caption[:self.max_caption_length-3] + "..."
        
        return caption
    
    async def _save_professional_cache_entry(self, video_info: Dict, telegram_file_id: str,
                                           content_type: str, quality: str, file_size: int, 
                                           content_hash: str):
        """Save comprehensive cache entry with professional metadata"""
        try:
            cache_collection = get_content_cache_collection()
            if cache_collection is None:
                logger.warning("Cache collection not available for saving entry")
                return
            
            cache_entry = {
                'youtube_id': video_info['video_id'],
                'title': video_info['title'],
                'duration': video_info['duration'],
                'telegram_file_id': telegram_file_id,
                'file_type': content_type,
                'quality': quality if content_type == 'video' else None,
                'file_size': file_size,
                'content_hash': content_hash,
                'status': 'active',
                'upload_date': datetime.utcnow().isoformat(),
                'created_at': datetime.utcnow(),
                'last_accessed': datetime.utcnow(),
                'last_verified': datetime.utcnow(),
                'access_count': 0,
                'metadata': {
                    'source_url': video_info.get('source_url'),
                    'thumbnail': video_info.get('thumbnail'),
                    'uploader': video_info.get('uploader', 'YouTube'),
                    'cache_version': '2.0'
                }
            }
            
            await cache_collection.insert_one(cache_entry)
            logger.info(f"💾 Professional cache entry saved: {video_info['video_id']}")
            
        except Exception as e:
            logger.error(f"Failed to save professional cache entry: {e}")
    
    async def professional_cleanup_cache(self, days: int = 30, max_inactive_days: int = 7):
        """Professional cache cleanup with comprehensive logic"""
        try:
            cache_collection = get_content_cache_collection()
            
            # Clean up old inactive entries
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            inactive_cutoff = datetime.utcnow() - timedelta(days=max_inactive_days)
            
            cleanup_query = {
                '$or': [
                    {
                        'created_at': {'$lt': cutoff_date},
                        'access_count': {'$lt': 5}  # Rarely accessed
                    },
                    {
                        'status': 'inactive',
                        'last_verified': {'$lt': inactive_cutoff}
                    }
                ]
            }
            
            if cache_collection is not None:
                deleted_count = await cache_collection.delete_many(cleanup_query)
                
                # Update statistics
                total_active = await cache_collection.count_documents({'status': 'active'})
                total_inactive = await cache_collection.count_documents({'status': 'inactive'})
            else:
                deleted_count = type('MockResult', (), {'deleted_count': 0})()
                total_active = 0
                total_inactive = 0
            
            logger.info(f"🧹 Professional cleanup complete:")
            logger.info(f"   - Removed: {deleted_count.deleted_count} entries")
            logger.info(f"   - Active: {total_active} entries")
            logger.info(f"   - Inactive: {total_inactive} entries")
            
        except Exception as e:
            logger.error(f"Professional cache cleanup failed: {e}")

# Global cache instance
telegram_cache = TelegramCache()
