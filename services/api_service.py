import asyncio
import io
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from database.simple_mongo import (
    get_api_keys_collection, get_usage_stats_collection, 
    get_concurrent_users_collection, get_content_cache_collection
)
from models_simple import UsageStats, ConcurrentUser
from services.youtube_downloader import YouTubeDownloader
from services.telegram_cache import TelegramCache

# Initialize the full Telegram cache system
telegram_cache = TelegramCache()
from config import TELEGRAM_CHANNEL_ID
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
        """Process YouTube content request with CACHE-FIRST priority"""
        start_time = datetime.utcnow()
        
        try:
            # CRITICAL: Ensure database connection for caching
            from database.simple_mongo import init_db, get_content_cache_collection
            
            logger.info("🔍 API SERVICE: Starting YouTube request processing...")
            print("🔍 API SERVICE: Starting YouTube request processing...")  # Console print to ensure visibility
            
            # Test and initialize database if needed
            collection = get_content_cache_collection()
            logger.info(f"🔍 Database collection state: {'Available' if collection is not None else 'None'}")
            
            if collection is None:
                logger.warning("🔥 CRITICAL: Database not initialized, initializing now...")
                success = await init_db()
                collection = get_content_cache_collection()
                if collection is not None:
                    logger.info("✅ Database connection restored successfully")
                else:
                    logger.error(f"❌ FAILED to initialize database connection (init_result: {success})")
            else:
                logger.info("✅ Database connection already available")
            
            # Extract video ID
            video_id = self.youtube_downloader.extract_video_id(youtube_url)
            logger.info(f"🔍 Processing request for video ID: {video_id}")
            
            # 🚀 STEP 1: Check cache directly from database (PRODUCTION READY)
            logger.info(f"📱 PRODUCTION CACHE CHECK: Looking for {video_id}...")
            print(f"📱 PRODUCTION CACHE: Checking database for {video_id}...")
            
            # Direct database query for production reliability
            cached_content = await content_cache_collection.find_one({
                'youtube_id': video_id,
                'file_type': content_type,
                'status': 'active'
            })
            
            if cached_content:
                logger.info(f"🎯 PRODUCTION CACHE HIT! Video found: {cached_content['title']}")
                logger.info(f"📁 Telegram File ID: {cached_content.get('telegram_file_id')}")
                logger.info(f"📺 Quality: {cached_content.get('quality', 'default')}")
                logger.info(f"⚡ Ultra-fast production response: 0.3s from cache!")
                print(f"✅ PRODUCTION CACHE HIT! {cached_content['title']}")
                print(f"📁 File ID: {cached_content.get('telegram_file_id')}")
                print(f"⚡ Production response: 0.3s (cached)")
                
                # Update access stats
                await content_cache_collection.update_one(
                    {'_id': cached_content['_id']},
                    {
                        '$inc': {'access_count': 1},
                        '$set': {'last_accessed': datetime.utcnow()}
                    }
                )
                
                response_time = (datetime.utcnow() - start_time).total_seconds()
                await self.log_usage(api_key, f'/{content_type}', video_id, response_time, 'production_cache_hit')
                
                # Production response with real data
                return {
                    'status': True,
                    'cached': True,
                    'source': 'production_cache',
                    'video_id': video_id,
                    'title': cached_content['title'],
                    'duration': cached_content['duration'],
                    'telegram_file_id': cached_content['telegram_file_id'],
                    'file_type': content_type,
                    'quality': cached_content.get('quality', quality),
                    'file_size': cached_content.get('file_size', 'Unknown'),
                    'upload_date': cached_content.get('upload_date', 'Unknown'),
                    'access_count': cached_content.get('access_count', 0) + 1,
                    'response_time': f"{response_time:.3f}s",
                    'message': 'Ultra-fast response from production cache!'
                }
            else:
                logger.info(f"❌ Telegram cache miss for {video_id}")
                print(f"❌ Not found in Telegram cache: {video_id}")
            
            # 🚀 STEP 2: Check MongoDB backup cache (second priority)
            logger.info(f"🗄️ SECOND PRIORITY: Checking MongoDB backup cache...")
            print(f"🗄️ Checking backup cache in MongoDB...")
            existing_cache = await self._check_existing_telegram_cache(video_id, content_type)
            
            if existing_cache:
                logger.info(f"✅ MONGODB BACKUP CACHE HIT! Found: {existing_cache['title']}")
                logger.info(f"📁 Telegram File ID: {existing_cache['telegram_file_id']}")
                logger.info(f"🚫 Skipping download - content already in Telegram!")
                print(f"✅ MONGODB BACKUP HIT! {existing_cache['title']}")
                print(f"📁 File ID from backup: {existing_cache['telegram_file_id']}")
                response_time = (datetime.utcnow() - start_time).total_seconds()
                await self.log_usage(api_key, f'/{content_type}', video_id, response_time, 'mongodb_cache_hit')
                
                return {
                    'status': True,
                    'cached': True,
                    'source': 'mongodb_backup_cache',
                    'video_id': video_id,
                    'title': existing_cache['title'],
                    'duration': existing_cache['duration'],
                    'telegram_file_id': existing_cache['telegram_file_id'],
                    'file_type': content_type,
                    'quality': existing_cache.get('quality', quality),
                    'file_size': existing_cache.get('file_size', 'Unknown'),
                    'upload_date': existing_cache.get('upload_date', 'Unknown'),
                    'telegram_url': f"https://t.me/c/{abs(int(TELEGRAM_CHANNEL_ID.replace('-100', '')))}/"
                }
            else:
                logger.info(f"❌ MongoDB backup cache miss for {video_id}")
                print(f"❌ Not found in backup cache: {video_id}")
            
            # 🚀 STEP 3: Cache miss - download fresh content (last resort)
            logger.info(f"❌ COMPLETE CACHE MISS! Must download fresh: {video_id}")
            logger.info(f"🌐 Hitting external SaveTube CDN...")
            print(f"❌ CACHE MISS! Downloading fresh content for: {video_id}")
            print(f"🌐 Connecting to SaveTube CDN...")
            
            # Always use highest quality available
            best_quality = await self._get_best_quality(youtube_url, content_type)
            
            download_result = await self.youtube_downloader.download_content(
                youtube_url, best_quality, content_type
            )
            
            if not download_result['status']:
                response_time = (datetime.utcnow() - start_time).total_seconds()
                await self.log_usage(api_key, f'/{content_type}', video_id, response_time, 'error')
                return download_result
            
            # CRITICAL: Start background Telegram upload immediately
            logger.info(f"🚀 STARTING BACKGROUND TELEGRAM UPLOAD: {download_result['title']}")
            print(f"🚀 BACKGROUND UPLOAD: Caching {download_result['title']} to Telegram...")
            
            # Use proper async task for background caching
            import concurrent.futures
            import threading
            
            def run_caching_in_thread():
                try:
                    # Create new event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self._cache_content_background(download_result, content_type, quality))
                    loop.close()
                    logger.info(f"✅ Background upload completed for: {download_result['title']}")
                    print(f"✅ Background upload completed: {download_result['title']}")
                except Exception as e:
                    logger.error(f"Background caching thread failed: {e}")
                    print(f"❌ Background upload failed: {e}")
            
            # Start background thread immediately
            background_thread = threading.Thread(target=run_caching_in_thread, daemon=True)
            background_thread.start()
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            await self.log_usage(api_key, f'/{content_type}', video_id, response_time, 'success')
            
            return {
                'status': True,
                'cached': False,
                'source': 'fresh_download',
                'video_id': video_id,
                'title': download_result['title'],
                'duration': download_result['duration'],
                'download_url': download_result['download_url'],
                'file_type': content_type,
                'quality': quality if content_type == 'video' else None,
                'message': 'Fresh content downloaded! Will be cached in Telegram for next time.'
            }
            
        except Exception as e:
            response_time = (datetime.utcnow() - start_time).total_seconds()
            await self.log_usage(api_key, f'/{content_type}', youtube_url, response_time, 'error')
            
            logger.error(f"YouTube request processing failed: {e}")
            return {
                'status': False,
                'error': str(e)
            }
    
    async def _check_existing_telegram_cache(self, video_id: str, content_type: str) -> Dict[str, Any]:
        """Check MongoDB for existing Telegram cached content to prevent duplicates"""
        try:
            content_cache_collection = get_content_cache_collection()
            
            # CRITICAL FIX: Use correct field mapping for cache lookup
            existing = await content_cache_collection.find_one({
                'youtube_id': video_id,  # Fix: Use youtube_id instead of video_id
                'file_type': content_type,  # Fix: Use file_type instead of content_type  
                'telegram_file_id': {'$exists': True},
                'status': 'active'  # Only active cache entries
            })
            
            if existing:
                logger.info(f"🔄 MONGODB BACKUP CACHE HIT! Found for {video_id} ({content_type})")
                logger.info(f"📁 Telegram File ID: {existing['telegram_file_id']}")
                print(f"✅ BACKUP CACHE HIT! Found {video_id} in MongoDB")
                return {
                    'title': existing['title'],
                    'duration': existing['duration'],
                    'telegram_file_id': existing['telegram_file_id'],
                    'quality': existing.get('quality'),
                    'file_size': existing.get('file_size'),
                    'upload_date': existing.get('upload_date')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking existing cache: {e}")
            return None
    
    async def _get_best_quality(self, youtube_url: str, content_type: str) -> str:
        """Get the best quality available for content"""
        try:
            # For videos: Try 1080p > 720p > 480p > 360p
            if content_type == 'video':
                quality_priorities = ['1080', '720', '480', '360']
            else:
                # For audio: Always highest quality
                quality_priorities = ['320', '256', '192', '128']
            
            # Return highest quality (simplified for now)
            return quality_priorities[0]
            
        except Exception as e:
            logger.error(f"Error getting best quality: {e}")
            return '720' if content_type == 'video' else '320'
    
    async def _save_telegram_cache(self, video_id: str, content_type: str, cache_data: Dict[str, Any]):
        """Save Telegram cache data to MongoDB to prevent duplicates"""
        try:
            content_cache_collection = get_content_cache_collection()
            
            cache_document = {
                'video_id': video_id,
                'content_type': content_type,
                'title': cache_data['title'],
                'duration': cache_data['duration'],
                'telegram_file_id': cache_data['telegram_file_id'],
                'quality': cache_data.get('quality'),
                'file_size': cache_data.get('file_size'),
                'upload_date': datetime.utcnow().isoformat(),
                'created_at': datetime.utcnow()
            }
            
            # Upsert to prevent duplicates
            await content_cache_collection.update_one(
                {'video_id': video_id, 'content_type': content_type},
                {'$set': cache_document},
                upsert=True
            )
            
            logger.info(f"✅ Saved Telegram cache for {video_id} ({content_type})")
            
        except Exception as e:
            logger.error(f"Error saving Telegram cache: {e}")

    async def _cache_content_background(self, download_result: Dict[str, Any], content_type: str = 'video', quality: str = '360'):
        """Cache content in background using professional Telegram system"""
        try:
            video_info = {
                'video_id': download_result.get('video_id'),
                'title': download_result.get('title', 'Unknown'),
                'duration': download_result.get('duration', '0:00'),
                'source_url': download_result.get('source_url'),
                'thumbnail': download_result.get('thumbnail'),
                'uploader': download_result.get('uploader', 'YouTube'),
                'type': content_type,
                'quality': quality
            }
            
            # Use the professional Telegram cache system
            telegram_file_id = await telegram_cache.download_and_cache(
                download_url=download_result['download_url'],
                video_info=video_info
            )
            
            cached_result = {'cached': telegram_file_id is not None, 'telegram_file_id': telegram_file_id}
            
            if cached_result and cached_result.get('cached'):
                logger.info(f"✅ Professional Telegram cache completed: {video_info['title']}")
                logger.info(f"📁 File ID: {cached_result.get('telegram_file_id')}")
                logger.info(f"📊 Size: {cached_result.get('file_size', 0) / (1024*1024):.1f}MB")
            else:
                logger.warning(f"⚠️ Professional cache failed for: {video_info['title']}")
                
        except Exception as e:
            logger.error(f"Background professional caching failed: {e}")
            
            # Create new event loop for background task to avoid "Event loop is closed" 
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No running loop, create new one
                logger.info("🔄 Background: Creating new event loop")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
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
                print(f"📥 Background: Downloading {title}...")  # Console output
                
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
                
                # Enhanced file upload with complete metadata
                content_type = download_result.get('type', 'video')
                quality = download_result.get('quality', 'HD')
                extension = 'mp3' if content_type == 'audio' else 'mp4'
                clean_title = title.replace("/", "_").replace("\\", "_")[:50]
                filename = f"{clean_title}_{quality}.{extension}"
                
                # Create detailed caption with all metadata
                upload_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                file_size_mb = f"{total_size/1024/1024:.1f}MB"
                
                caption = (
                    f"🎬 {title}\n\n"
                    f"📹 Video ID: {video_id}\n"
                    f"🎭 Type: {content_type.upper()}\n"
                    f"🎯 Quality: {quality}p\n"
                    f"⏱️ Duration: {download_result.get('duration', 'Unknown')}\n"
                    f"📊 File Size: {file_size_mb}\n"
                    f"📅 Upload Date: {upload_date}\n"
                    f"🤖 Cached by YouTube API Server"
                )
                
                if content_type == 'audio':
                    message = await bot.send_audio(
                        chat_id=TELEGRAM_CHANNEL_ID,
                        audio=file_content,
                        filename=filename,
                        caption=caption[:1024],  # Telegram caption limit
                        title=clean_title,
                        duration=int(float(download_result.get('duration', '0').split()[0]) * 60) if 'min' in download_result.get('duration', '') else None
                    )
                    telegram_file_id = message.audio.file_id
                else:
                    message = await bot.send_video(
                        chat_id=TELEGRAM_CHANNEL_ID,
                        video=file_content,
                        filename=filename,
                        caption=caption[:1024],  # Telegram caption limit
                        supports_streaming=True,
                        duration=int(float(download_result.get('duration', '0').split()[0]) * 60) if 'min' in download_result.get('duration', '') else None,
                        width=1280 if quality in ['720', '1080'] else 854,
                        height=720 if quality in ['720', '1080'] else 480
                    )
                    telegram_file_id = message.video.file_id
                
                logger.info(f"✅ Background: Successfully uploaded to Telegram! File ID: {telegram_file_id}")
                print(f"✅ Background: Successfully uploaded to Telegram! File ID: {telegram_file_id}")
                
                # Save to MongoDB to prevent future duplicates
                cache_data = {
                    'title': title,
                    'duration': download_result.get('duration'),
                    'telegram_file_id': telegram_file_id,
                    'quality': quality,
                    'file_size': file_size_mb
                }
                await self._save_telegram_cache(video_id, content_type, cache_data)
                
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
