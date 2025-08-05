import asyncio
import io
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from database.mongo import (
    get_api_keys_collection, get_usage_stats_collection, 
    get_concurrent_users_collection
)
from models import UsageStats, ConcurrentUser
from services.youtube_downloader import YouTubeDownloader
from services.telegram_cache import telegram_cache
from utils.logging import LOGGER

logger = LOGGER(__name__)

class APIService:
    def __init__(self):
        self.youtube_downloader = YouTubeDownloader()
        self.active_sessions = {}  # Track concurrent users
        
    async def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key and check rate limits"""
        try:
            api_keys_collection = get_api_keys_collection()
            
            key_data = await api_keys_collection.find_one({
                'key': api_key,
                'is_active': True
            })
            
            if not key_data:
                return None
            
            # Check rate limit
            usage_stats_collection = get_usage_stats_collection()
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            usage_count = await usage_stats_collection.count_documents({
                'api_key': api_key,
                'timestamp': {'$gte': one_hour_ago}
            })
            
            if usage_count >= key_data.get('rate_limit', 1000):
                return {'error': 'Rate limit exceeded'}
            
            # Update last used
            await api_keys_collection.update_one(
                {'key': api_key},
                {
                    '$set': {'last_used': datetime.utcnow()},
                    '$inc': {'usage_count': 1}
                }
            )
            
            return key_data
            
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return None
    
    async def log_usage(self, api_key: str, endpoint: str, youtube_id: str = None, 
                       response_time: float = None, status: str = 'success'):
        """Log API usage for analytics"""
        try:
            usage_stat = UsageStats(
                api_key=api_key,
                endpoint=endpoint,
                youtube_id=youtube_id
            )
            usage_stat.response_time = response_time
            usage_stat.status = status
            
            usage_stats_collection = get_usage_stats_collection()
            await usage_stats_collection.insert_one(usage_stat.to_dict())
            
        except Exception as e:
            logger.error(f"Usage logging failed: {e}")
    
    async def register_concurrent_user(self, session_id: str, api_key: str, endpoint: str):
        """Register a concurrent user session"""
        try:
            concurrent_user = ConcurrentUser(
                session_id=session_id,
                api_key=api_key,
                endpoint=endpoint
            )
            
            concurrent_users_collection = get_concurrent_users_collection()
            await concurrent_users_collection.insert_one(concurrent_user.to_dict())
            
            # Track in memory for real-time monitoring
            self.active_sessions[session_id] = {
                'api_key': api_key,
                'endpoint': endpoint,
                'connected_at': datetime.utcnow()
            }
            
            logger.info(f"Concurrent user registered: {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to register concurrent user: {e}")
    
    async def unregister_concurrent_user(self, session_id: str):
        """Unregister a concurrent user session"""
        try:
            concurrent_users_collection = get_concurrent_users_collection()
            await concurrent_users_collection.delete_one({'session_id': session_id})
            
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            logger.info(f"Concurrent user unregistered: {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to unregister concurrent user: {e}")
    
    async def get_concurrent_user_count(self) -> int:
        """Get current concurrent user count"""
        try:
            # Clean up old sessions (older than 1 hour)
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            concurrent_users_collection = get_concurrent_users_collection()
            
            await concurrent_users_collection.delete_many({
                'last_activity': {'$lt': one_hour_ago}
            })
            
            # Count active sessions
            count = await concurrent_users_collection.count_documents({})
            return count
            
        except Exception as e:
            logger.error(f"Failed to get concurrent user count: {e}")
            return 0
    
    async def process_youtube_request(self, api_key: str, youtube_url: str, 
                                    content_type: str = 'video', quality: str = '360') -> Dict[str, Any]:
        """Process YouTube content request with caching"""
        start_time = datetime.utcnow()
        
        try:
            # Extract video ID
            video_id = self.youtube_downloader.extract_video_id(youtube_url)
            
            # Check cache first
            cached_content = await telegram_cache.check_cache(video_id, content_type, quality)
            
            if cached_content:
                response_time = (datetime.utcnow() - start_time).total_seconds()
                await self.log_usage(api_key, f'/{content_type}', video_id, response_time, 'cache_hit')
                
                return {
                    'status': True,
                    'cached': True,
                    'video_id': video_id,
                    'title': cached_content['title'],
                    'duration': cached_content['duration'],
                    'telegram_file_id': cached_content['telegram_file_id'],
                    'file_type': content_type,
                    'quality': quality if content_type == 'video' else None,
                    'stream_url': await telegram_cache.get_file_stream_url(cached_content['telegram_file_id'])
                }
            
            # Not in cache, download from YouTube
            logger.info(f"Downloading from YouTube: {video_id}")
            download_result = await self.youtube_downloader.download_content(
                youtube_url, quality, content_type
            )
            
            if not download_result['status']:
                response_time = (datetime.utcnow() - start_time).total_seconds()
                await self.log_usage(api_key, f'/{content_type}', video_id, response_time, 'error')
                return download_result
            
            # Cache the content in background with MongoDB Atlas
            asyncio.create_task(self._cache_content_background(download_result))
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            await self.log_usage(api_key, f'/{content_type}', video_id, response_time, 'success')
            
            return {
                'status': True,
                'cached': False,
                'video_id': video_id,
                'title': download_result['title'],
                'duration': download_result['duration'],
                'download_url': download_result['download_url'],
                'file_type': content_type,
                'quality': quality if content_type == 'video' else None,
                'message': 'Content will be cached for future requests'
            }
            
        except Exception as e:
            response_time = (datetime.utcnow() - start_time).total_seconds()
            await self.log_usage(api_key, f'/{content_type}', youtube_url, response_time, 'error')
            
            logger.error(f"YouTube request processing failed: {e}")
            return {
                'status': False,
                'error': str(e)
            }
    
    async def _cache_content_background(self, download_result: Dict[str, Any]):
        """Background task - Download file and upload to Telegram"""
        try:
            video_id = download_result['video_id']
            title = download_result['title']
            download_url = download_result['download_url']
            
            logger.info(f"🔄 Background: Starting download for {title}")
            
            # Download the file
            session = httpx.AsyncClient(timeout=300.0)
            
            async with session.stream('GET', download_url) as response:
                if response.status_code != 200:
                    logger.error(f"❌ Background: Download failed {response.status_code}")
                    return
                
                # Create in-memory file for Telegram upload
                file_content = io.BytesIO()
                total_size = 0
                
                logger.info(f"📥 Background: Downloading {title}...")
                
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    file_content.write(chunk)
                    total_size += len(chunk)
                    
                    # Size limit for Telegram (50MB)
                    if total_size > 50 * 1024 * 1024:
                        logger.warning(f"⚠️ Background: File too large ({total_size/1024/1024:.1f}MB) for Telegram")
                        await session.aclose()
                        return
                
                file_content.seek(0)
                await session.aclose()
                
                logger.info(f"📤 Background: Downloaded {total_size/1024/1024:.1f}MB, uploading to Telegram...")
                
                # Upload to Telegram
                from telegram import Bot
                from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID
                
                bot = Bot(token=TELEGRAM_BOT_TOKEN)
                
                # Determine file type and upload
                content_type = download_result.get('type', 'video')
                quality = download_result.get('quality', '360')
                extension = 'mp3' if content_type == 'audio' else 'mp4'
                filename = f"{title[:50]}.{extension}"
                
                if content_type == 'audio':
                    message = await bot.send_audio(
                        chat_id=TELEGRAM_CHANNEL_ID,
                        audio=file_content,
                        title=title,
                        filename=filename,
                        caption=f"🎵 {title}\nVideo ID: {video_id}"
                    )
                    telegram_file_id = message.audio.file_id
                else:
                    message = await bot.send_video(
                        chat_id=TELEGRAM_CHANNEL_ID,
                        video=file_content,
                        caption=f"🎬 {title}\nQuality: {quality}p\nVideo ID: {video_id}",
                        filename=filename
                    )
                    telegram_file_id = message.video.file_id
                
                logger.info(f"✅ Background: Successfully uploaded to Telegram! File ID: {telegram_file_id}")
                
        except Exception as e:
            logger.error(f"❌ Background caching error: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
    
    async def get_analytics_data(self, hours: int = 24) -> Dict[str, Any]:
        """Get analytics data for admin dashboard"""
        try:
            time_ago = datetime.utcnow() - timedelta(hours=hours)
            
            usage_stats_collection = get_usage_stats_collection()
            api_keys_collection = get_api_keys_collection()
            
            # Total requests
            total_requests = await usage_stats_collection.count_documents({
                'timestamp': {'$gte': time_ago}
            })
            
            # Requests by endpoint
            pipeline = [
                {'$match': {'timestamp': {'$gte': time_ago}}},
                {'$group': {'_id': '$endpoint', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}}
            ]
            endpoint_stats = await usage_stats_collection.aggregate(pipeline).to_list(None)
            
            # Top API keys
            pipeline = [
                {'$match': {'timestamp': {'$gte': time_ago}}},
                {'$group': {'_id': '$api_key', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}},
                {'$limit': 10}
            ]
            top_api_keys = await usage_stats_collection.aggregate(pipeline).to_list(None)
            
            # Total API keys
            total_api_keys = await api_keys_collection.count_documents({'is_active': True})
            
            # Current concurrent users
            concurrent_users = await self.get_concurrent_user_count()
            
            # Cache hit rate
            cache_hits = await usage_stats_collection.count_documents({
                'timestamp': {'$gte': time_ago},
                'status': 'cache_hit'
            })
            cache_hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'total_requests': total_requests,
                'endpoint_stats': endpoint_stats,
                'top_api_keys': top_api_keys,
                'total_api_keys': total_api_keys,
                'concurrent_users': concurrent_users,
                'cache_hit_rate': round(cache_hit_rate, 2),
                'time_period_hours': hours
            }
            
        except Exception as e:
            logger.error(f"Analytics data retrieval failed: {e}")
            return {}

# Global API service instance
api_service = APIService()
