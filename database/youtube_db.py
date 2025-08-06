"""
Professional YouTube API Database Operations
Similar to the music bot system but for YouTube API management
"""

import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Union, Optional
from pymongo import MongoClient
import os
import logging

from database.simple_mongo import mongo_db

logger = logging.getLogger(__name__)

# Database collections
api_keys_db = mongo_db.db.api_keys if mongo_db.db else None
users_db = mongo_db.db.users if mongo_db.db else None
usage_stats_db = mongo_db.db.usage_stats if mongo_db.db else None
content_cache_db = mongo_db.db.content_cache if mongo_db.db else None
concurrent_users_db = mongo_db.db.concurrent_users if mongo_db.db else None
admin_sessions_db = mongo_db.db.admin_sessions if mongo_db.db else None
blacklist_db = mongo_db.db.blacklisted_users if mongo_db.db else None
analytics_db = mongo_db.db.analytics if mongo_db.db else None

# Memory cache for performance
active_api_keys = {}
cached_users = {}
admin_sessions = {}
api_key_usage = {}
system_stats = {}


class YouTubeDatabaseManager:
    """Professional database manager for YouTube API server"""
    
    def __init__(self):
        self.mongodb_uri = os.getenv("MONGO_DB_URI", "mongodb+srv://jaydipmore74:xCpTm5OPAfRKYnif@cluster0.5jo18.mongodb.net/?retryWrites=true&w=majority")
    
    def _get_sync_client(self):
        """Get synchronous MongoDB client"""
        return MongoClient(self.mongodb_uri)
    
    # ==================== API KEYS MANAGEMENT ====================
    
    async def create_api_key(self, user_id: str, name: str, rate_limit: int = 1000, expires_days: int = 365) -> Optional[str]:
        """Create new API key with professional features"""
        try:
            from models_simple import APIKey, User
            
            sync_client = self._get_sync_client()
            db = sync_client.youtube_api_db
            
            # Check if user exists, create if not
            user = db.users.find_one({'_id': user_id})
            if not user:
                new_user = User(username=f'user_{user_id[:8]}', email=f'user_{user_id[:8]}@example.com', _id=user_id)
                db.users.insert_one(new_user.to_dict())
                logger.info(f"✓ Created new user: {user_id}")
            
            # Create API key with expiry
            api_key = APIKey(user_id=user_id, name=name, rate_limit=rate_limit)
            
            key_data = api_key.to_dict()
            key_data.update({
                'expires_at': datetime.utcnow() + timedelta(days=expires_days),
                'last_used': None,
                'request_count': 0,
                'status': 'active',
                'permissions': ['read', 'download', 'stream'],
                'created_by': 'admin',
                'notes': f'API key for {name}',
                'ip_whitelist': [],
                'domain_restrictions': []
            })
            
            # Insert into database
            result = db.api_keys.insert_one(key_data)
            
            if result.inserted_id:
                # Cache the key
                active_api_keys[api_key.key] = key_data
                
                # Log creation event
                db.api_key_usage.insert_one({
                    'api_key_id': key_data['_id'],
                    'event': 'created',
                    'timestamp': datetime.utcnow(),
                    'details': f'API key {name} created for user {user_id}',
                    'ip_address': None,
                    'user_agent': None
                })
                
                sync_client.close()
                logger.info(f"✅ API key created successfully: {api_key.key[:12]}... for user {user_id}")
                return api_key.key
            
            sync_client.close()
            return None
            
        except Exception as e:
            logger.error(f"❌ API key creation failed: {e}")
            return None
    
    def get_all_api_keys_sync(self) -> List[Dict]:
        """Get all API keys synchronously"""
        try:
            sync_client = self._get_sync_client()
            db = sync_client.youtube_api_db
            
            cursor = db.api_keys.find({}).sort("created_at", -1)
            api_keys = list(cursor)
            
            # Format for template
            for key in api_keys:
                if 'created_at' in key and isinstance(key['created_at'], datetime):
                    key['created_at'] = key['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                if 'expires_at' in key and key['expires_at']:
                    key['is_expired'] = datetime.utcnow() > key['expires_at']
                    key['expires_at'] = key['expires_at'].strftime('%Y-%m-%d %H:%M:%S')
                else:
                    key['is_expired'] = False
                
                # Security: Hide full key
                if 'key' in key:
                    key['key_preview'] = key['key'][:12] + '...'
            
            sync_client.close()
            logger.info(f"✓ Retrieved {len(api_keys)} API keys")
            return api_keys
            
        except Exception as e:
            logger.error(f"❌ Error retrieving API keys: {e}")
            return []
    
    def toggle_api_key_sync(self, key_id: str) -> bool:
        """Toggle API key status synchronously"""
        try:
            sync_client = self._get_sync_client()
            db = sync_client.youtube_api_db
            
            key_data = db.api_keys.find_one({'_id': key_id})
            if key_data:
                new_status = not key_data.get('is_active', True)
                result = db.api_keys.update_one(
                    {'_id': key_id},
                    {'$set': {'is_active': new_status, 'updated_at': datetime.utcnow()}}
                )
                
                # Log the event
                db.api_key_usage.insert_one({
                    'api_key_id': key_id,
                    'event': 'status_changed',
                    'timestamp': datetime.utcnow(),
                    'details': f'API key {"activated" if new_status else "deactivated"}',
                    'new_status': new_status
                })
                
                sync_client.close()
                
                if result.modified_count > 0:
                    logger.info(f"✓ API key {key_id} {'activated' if new_status else 'deactivated'}")
                    return True
            
            sync_client.close()
            return False
            
        except Exception as e:
            logger.error(f"❌ Error toggling API key: {e}")
            return False
    
    def delete_api_key_sync(self, key_id: str) -> bool:
        """Delete API key synchronously"""
        try:
            sync_client = self._get_sync_client()
            db = sync_client.youtube_api_db
            
            # Log deletion before removing
            key_data = db.api_keys.find_one({'_id': key_id})
            if key_data:
                db.api_key_usage.insert_one({
                    'api_key_id': key_id,
                    'event': 'deleted',
                    'timestamp': datetime.utcnow(),
                    'details': f'API key {key_data.get("name", "Unknown")} deleted',
                    'deleted_key_name': key_data.get('name')
                })
            
            result = db.api_keys.delete_one({'_id': key_id})
            sync_client.close()
            
            if result.deleted_count > 0:
                logger.info(f"✓ API key {key_id} deleted successfully")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error deleting API key: {e}")
            return False
    
    # ==================== USER MANAGEMENT ====================
    
    def get_all_users_sync(self) -> List[Dict]:
        """Get all users synchronously"""
        try:
            sync_client = self._get_sync_client()
            db = sync_client.youtube_api_db
            
            cursor = db.users.find({}).sort("created_at", -1)
            users = list(cursor)
            
            # Format for template
            for user in users:
                if 'created_at' in user and isinstance(user['created_at'], datetime):
                    user['created_at'] = user['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            sync_client.close()
            logger.info(f"✓ Retrieved {len(users)} users")
            return users
            
        except Exception as e:
            logger.error(f"❌ Error retrieving users: {e}")
            return []
    
    async def is_user_exists(self, user_id: str) -> bool:
        """Check if user exists"""
        try:
            sync_client = self._get_sync_client()
            db = sync_client.youtube_api_db
            
            user = db.users.find_one({'_id': user_id})
            sync_client.close()
            return bool(user)
            
        except Exception as e:
            logger.error(f"❌ Error checking user existence: {e}")
            return False
    
    async def add_user(self, user_id: str, username: str, email: str) -> bool:
        """Add new user"""
        try:
            from models_simple import User
            
            sync_client = self._get_sync_client()
            db = sync_client.youtube_api_db
            
            # Check if user already exists
            if db.users.find_one({'_id': user_id}):
                sync_client.close()
                return True
            
            new_user = User(username=username, email=email, _id=user_id)
            result = db.users.insert_one(new_user.to_dict())
            sync_client.close()
            
            if result.inserted_id:
                logger.info(f"✓ User {user_id} added successfully")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error adding user: {e}")
            return False
    
    # ==================== USAGE STATISTICS ====================
    
    async def record_api_usage(self, api_key: str, endpoint: str, success: bool = True, response_time: float = 0):
        """Record API usage statistics"""
        try:
            sync_client = self._get_sync_client()
            db = sync_client.youtube_api_db
            
            usage_data = {
                'api_key': api_key[:12] + '...',  # Security: don't store full key
                'endpoint': endpoint,
                'timestamp': datetime.utcnow(),
                'success': success,
                'response_time_ms': response_time,
                'date': datetime.utcnow().strftime('%Y-%m-%d'),
                'hour': datetime.utcnow().hour
            }
            
            db.usage_stats.insert_one(usage_data)
            
            # Update API key last used
            db.api_keys.update_one(
                {'key': api_key},
                {'$set': {'last_used': datetime.utcnow()}, '$inc': {'request_count': 1}}
            )
            
            sync_client.close()
            
        except Exception as e:
            logger.error(f"❌ Error recording API usage: {e}")
    
    def get_usage_analytics_sync(self, days: int = 7) -> Dict:
        """Get usage analytics synchronously"""
        try:
            sync_client = self._get_sync_client()
            db = sync_client.youtube_api_db
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Total requests
            total_requests = db.usage_stats.count_documents({'timestamp': {'$gte': start_date}})
            
            # Success rate
            successful_requests = db.usage_stats.count_documents({
                'timestamp': {'$gte': start_date},
                'success': True
            })
            
            success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
            
            # Popular endpoints
            pipeline = [
                {'$match': {'timestamp': {'$gte': start_date}}},
                {'$group': {'_id': '$endpoint', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}},
                {'$limit': 10}
            ]
            
            popular_endpoints = list(db.usage_stats.aggregate(pipeline))
            
            sync_client.close()
            
            return {
                'total_requests': total_requests,
                'success_rate': round(success_rate, 2),
                'popular_endpoints': popular_endpoints,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting usage analytics: {e}")
            return {'total_requests': 0, 'success_rate': 0, 'popular_endpoints': [], 'period_days': days}
    
    # ==================== ADMIN AUTHENTICATION ====================
    
    def create_admin_session(self, username: str, ip_address: str = None) -> str:
        """Create admin session"""
        try:
            import uuid
            
            sync_client = self._get_sync_client()
            db = sync_client.youtube_api_db
            
            session_id = str(uuid.uuid4())
            session_data = {
                'session_id': session_id,
                'username': username,
                'ip_address': ip_address,
                'created_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(hours=8),
                'last_activity': datetime.utcnow(),
                'is_active': True
            }
            
            db.admin_sessions.insert_one(session_data)
            admin_sessions[session_id] = session_data
            
            sync_client.close()
            logger.info(f"✓ Admin session created for {username}")
            return session_id
            
        except Exception as e:
            logger.error(f"❌ Error creating admin session: {e}")
            return None
    
    def validate_admin_session(self, session_id: str) -> bool:
        """Validate admin session"""
        try:
            # Check memory cache first
            if session_id in admin_sessions:
                session = admin_sessions[session_id]
                if session['expires_at'] > datetime.utcnow() and session['is_active']:
                    return True
            
            # Check database
            sync_client = self._get_sync_client()
            db = sync_client.youtube_api_db
            
            session = db.admin_sessions.find_one({
                'session_id': session_id,
                'is_active': True,
                'expires_at': {'$gt': datetime.utcnow()}
            })
            
            sync_client.close()
            return bool(session)
            
        except Exception as e:
            logger.error(f"❌ Error validating admin session: {e}")
            return False


# Global database manager instance
youtube_db = YouTubeDatabaseManager()


# ==================== CONVENIENCE FUNCTIONS ====================

async def create_api_key(user_id: str, name: str, rate_limit: int = 1000) -> Optional[str]:
    """Create API key - async wrapper"""
    return await youtube_db.create_api_key(user_id, name, rate_limit)

def get_all_api_keys() -> List[Dict]:
    """Get all API keys - sync"""
    return youtube_db.get_all_api_keys_sync()

def get_all_users() -> List[Dict]:
    """Get all users - sync"""
    return youtube_db.get_all_users_sync()

def toggle_api_key(key_id: str) -> bool:
    """Toggle API key status - sync"""
    return youtube_db.toggle_api_key_sync(key_id)

def delete_api_key(key_id: str) -> bool:
    """Delete API key - sync"""
    return youtube_db.delete_api_key_sync(key_id)

def get_usage_analytics(days: int = 7) -> Dict:
    """Get usage analytics - sync"""
    return youtube_db.get_usage_analytics_sync(days)

async def record_api_usage(api_key: str, endpoint: str, success: bool = True, response_time: float = 0):
    """Record API usage"""
    await youtube_db.record_api_usage(api_key, endpoint, success, response_time)