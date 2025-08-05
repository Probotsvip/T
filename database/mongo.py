from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from config import MONGO_DB_URI
from utils.logging import LOGGER

logger = LOGGER(__name__)

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None
        
    async def connect(self):
        """Connect to MongoDB with connection pooling"""
        try:
            logger.info("Connecting to MongoDB...")
            self.client = AsyncIOMotorClient(
                MONGO_DB_URI,
                maxPoolSize=100,  # Support high concurrency
                minPoolSize=10,
                maxIdleTimeMS=30000,
                waitQueueMultiple=10000  # Support 10k+ concurrent users
            )
            self.db = self.client.youtube_api
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Global MongoDB instance
mongodb = MongoDB()

# Initialize connection
async def init_db():
    await mongodb.connect()

# Collections
def get_users_collection():
    return mongodb.db.users

def get_api_keys_collection():
    return mongodb.db.api_keys

def get_content_cache_collection():
    return mongodb.db.content_cache

def get_usage_stats_collection():
    return mongodb.db.usage_stats

def get_concurrent_users_collection():
    return mongodb.db.concurrent_users
