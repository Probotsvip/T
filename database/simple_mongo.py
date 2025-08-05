import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import asyncio
from utils.logging import LOGGER

logger = LOGGER(__name__)

class MongoDB:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            mongo_uri = os.getenv("MONGO_DB_URI", "mongodb+srv://jaydipmore74:xCpTm5OPAfRKYnif@cluster0.5jo18.mongodb.net/?retryWrites=true&w=majority")
            
            self.client = AsyncIOMotorClient(
                mongo_uri,
                maxPoolSize=50,
                minPoolSize=5,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                retryWrites=True,
                retryReads=True
            )
            
            self.db = self.client.youtube_api_db
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("Connected to MongoDB successfully")
            return True
            
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            return False
    
    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None

# Global MongoDB instance
mongo_db = MongoDB()

async def init_db():
    """Initialize database connection"""
    return await mongo_db.connect()

def get_db():
    """Get database instance"""
    return mongo_db.db

def get_users_collection():
    """Get users collection"""
    db = get_db()
    if db is not None:
        return db.users
    return None

def get_api_keys_collection():
    """Get api_keys collection"""
    db = get_db()
    if db is not None:
        return db.api_keys
    return None

def get_content_cache_collection():
    """Get content_cache collection"""
    db = get_db()
    if db is not None:
        return db.content_cache
    return None

def get_usage_stats_collection():
    """Get usage_stats collection"""
    db = get_db()
    if db is not None:
        return db.usage_stats
    return None

def get_concurrent_users_collection():
    """Get concurrent_users collection"""
    db = get_db()
    if db is not None:
        return db.concurrent_users
    return None