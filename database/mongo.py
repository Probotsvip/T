from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import time
from typing import Optional
from config import MONGO_DB_URI
from utils.logging import LOGGER

logger = LOGGER(__name__)

class ProfessionalMongoDB:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.connection_pool_ready = False
        self.last_health_check = 0
        self.health_check_interval = 30  # 30 seconds
        self.retry_attempts = 5
        self.retry_delays = [1, 2, 5, 10, 30]  # Exponential backoff
        
    async def connect(self):
        """Professional MongoDB connection with persistent pooling and auto-recovery"""
        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"🔄 Professional MongoDB connection attempt {attempt + 1}/{self.retry_attempts}")
                
                # Professional connection configuration for maximum stability
                self.client = AsyncIOMotorClient(
                    MONGO_DB_URI,
                    # Connection Pool Settings (Professional Grade)
                    maxPoolSize=200,  # Increased for high concurrency
                    minPoolSize=20,   # Always maintain minimum connections
                    maxIdleTimeMS=300000,  # 5 minutes idle time
                    
                    # Timeout Settings (Optimized for stability)
                    serverSelectionTimeoutMS=5000,  # 5 seconds selection
                    connectTimeoutMS=5000,   # 5 seconds connect
                    
                    # Professional Reliability Features
                    retryWrites=True,         # Auto-retry failed writes
                    retryReads=True,          # Auto-retry failed reads
                    
                    # Advanced Connection Management
                    heartbeatFrequencyMS=10000,  # Heartbeat every 10 seconds
                    appName="YouTube-API-Professional-Server"
                )
                
                self.db = self.client.youtube_api_professional
                
                # Professional connection validation with comprehensive testing
                await asyncio.wait_for(self._validate_connection_health(), timeout=15.0)
                
                self.connection_pool_ready = True
                self.last_health_check = time.time()
                
                logger.info("🚀 Professional MongoDB connection established successfully!")
                logger.info(f"📊 Connection Pool: Min={50}, Max={200} connections")
                logger.info(f"🎯 Database: {self.db.name}")
                
                # Start background health monitoring
                asyncio.create_task(self._background_health_monitor())
                
                return True
                
            except Exception as e:
                logger.error(f"❌ Connection attempt {attempt + 1} failed: {e}")
                if attempt < self.retry_attempts - 1:
                    delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    logger.info(f"⏳ Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error("🔴 All MongoDB connection attempts failed!")
                    raise
    
    async def _validate_connection_health(self):
        """Comprehensive connection health validation"""
        # Test 1: Basic ping
        await self.client.admin.command('ping')
        
        # Test 2: Database access
        await self.db.command('ping')
        
        # Test 3: Collection operations
        test_collection = self.db.connection_test
        test_doc = {'test': True, 'timestamp': time.time()}
        await test_collection.insert_one(test_doc)
        await test_collection.delete_one({'test': True})
        
        # Test 4: Index creation (ensures write permissions)
        await test_collection.create_index('timestamp')
        
        logger.info("✅ All connection health checks passed")
    
    async def _background_health_monitor(self):
        """Background task to monitor connection health"""
        while self.connection_pool_ready:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                current_time = time.time()
                if current_time - self.last_health_check > self.health_check_interval:
                    await self.client.admin.command('ping')
                    self.last_health_check = current_time
                    logger.debug("🔄 Background health check passed")
                    
            except Exception as e:
                logger.warning(f"⚠️ Background health check failed: {e}")
                # Attempt to reconnect if health check fails
                try:
                    await self.connect()
                except Exception as reconnect_error:
                    logger.error(f"🔴 Reconnection failed: {reconnect_error}")
    
    async def get_connection_stats(self):
        """Get professional connection statistics"""
        if not self.client:
            return None
            
        try:
            server_status = await self.db.command('serverStatus')
            return {
                'connection_pool_ready': self.connection_pool_ready,
                'connections_active': server_status.get('connections', {}).get('current', 0),
                'connections_available': server_status.get('connections', {}).get('available', 0),
                'last_health_check': self.last_health_check,
                'uptime_seconds': server_status.get('uptime', 0),
                'database_name': self.db.name
            }
        except Exception:
            return {'connection_pool_ready': self.connection_pool_ready}
    
    async def close(self):
        """Graceful MongoDB connection closure"""
        if self.client:
            self.connection_pool_ready = False
            self.client.close()
            logger.info("🔴 Professional MongoDB connection closed")

    async def ensure_connection(self):
        """Ensure connection is alive, reconnect if needed"""
        if not self.connection_pool_ready or not self.client:
            await self.connect()
        
        try:
            await self.client.admin.command('ping')
        except Exception:
            logger.warning("🔄 Connection lost, reconnecting...")
            await self.connect()

# Global Professional MongoDB instance
mongodb = ProfessionalMongoDB()

# Professional initialization
async def init_professional_db():
    """Initialize professional database with comprehensive setup"""
    await mongodb.connect()
    
    # Create indexes for optimal performance
    await _create_professional_indexes()

async def _create_professional_indexes():
    """Create professional indexes for optimal query performance"""
    try:
        # Content cache indexes
        cache_collection = mongodb.db.content_cache
        await cache_collection.create_index([("youtube_id", 1), ("file_type", 1)], background=True)
        await cache_collection.create_index([("status", 1), ("created_at", -1)], background=True)
        await cache_collection.create_index([("content_hash", 1)], unique=True, background=True)
        
        # Usage stats indexes
        usage_collection = mongodb.db.usage_stats
        await usage_collection.create_index([("api_key", 1), ("timestamp", -1)], background=True)
        await usage_collection.create_index([("endpoint", 1), ("timestamp", -1)], background=True)
        
        # API keys indexes
        api_keys_collection = mongodb.db.api_keys
        await api_keys_collection.create_index([("key", 1)], unique=True, background=True)
        await api_keys_collection.create_index([("active", 1), ("created_at", -1)], background=True)
        
        # Concurrent users indexes
        concurrent_collection = mongodb.db.concurrent_users
        await concurrent_collection.create_index([("last_activity", 1)], background=True)
        
        logger.info("🚀 Professional database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Index creation failed: {e}")

# Professional Collections with auto-reconnection
async def get_users_collection():
    await mongodb.ensure_connection()
    return mongodb.db.users

async def get_api_keys_collection():
    await mongodb.ensure_connection()
    return mongodb.db.api_keys

async def get_content_cache_collection():
    await mongodb.ensure_connection()
    return mongodb.db.content_cache

async def get_usage_stats_collection():
    await mongodb.ensure_connection()
    return mongodb.db.usage_stats

async def get_concurrent_users_collection():
    await mongodb.ensure_connection()
    return mongodb.db.concurrent_users

# Backward compatibility (sync versions for existing code)
def get_content_cache_collection():
    return mongodb.db.content_cache

def get_users_collection():
    return mongodb.db.users

def get_api_keys_collection():
    return mongodb.db.api_keys

def get_usage_stats_collection():
    return mongodb.db.usage_stats

def get_concurrent_users_collection():
    return mongodb.db.concurrent_users
