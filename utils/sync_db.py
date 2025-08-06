"""
Synchronous database operations helper
Professional-grade MongoDB operations for admin panel
"""

import logging
from pymongo.errors import PyMongoError
from database.simple_mongo import get_api_keys_collection, get_users_collection
from models_simple import User, APIKey
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pymongo

logger = logging.getLogger(__name__)

class SyncDatabase:
    """Synchronous database operations for admin panel"""
    
    @staticmethod
    def get_all_api_keys() -> List[Dict[str, Any]]:
        """Get all API keys synchronously"""
        try:
            from database.simple_mongo import mongo_db
            
            if mongo_db.db is None:
                logger.error("Database not connected")
                return []
            
            # Create synchronous MongoDB client directly
            import os
            from pymongo import MongoClient
            
            mongodb_uri = os.getenv("MONGO_DB_URI", "mongodb+srv://jaydipmore74:xCpTm5OPAfRKYnif@cluster0.5jo18.mongodb.net/?retryWrites=true&w=majority")
            sync_client = MongoClient(mongodb_uri)
            sync_db = sync_client.youtube_api_db
            collection = sync_db.api_keys
            
            # Use synchronous find operation
            cursor = collection.find({}).sort("created_at", -1)
            api_keys = list(cursor)
            sync_client.close()
            
            # Convert datetime objects to strings for template rendering
            for key in api_keys:
                if 'created_at' in key and isinstance(key['created_at'], datetime):
                    key['created_at'] = key['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                # Check expiry status
                if 'expires_at' in key and key['expires_at']:
                    key['is_expired'] = datetime.utcnow() > key['expires_at']
                else:
                    key['is_expired'] = False
                    
                # Hide full API key for security
                if 'key' in key:
                    key['key_preview'] = key['key'][:12] + '...'
            
            logger.info(f"Retrieved {len(api_keys)} API keys successfully")
            return api_keys
            
        except Exception as e:
            logger.error(f"Error retrieving API keys: {e}")
            return []
    
    @staticmethod
    def get_all_users() -> List[Dict[str, Any]]:
        """Get all users synchronously"""
        try:
            # Create synchronous MongoDB client directly
            import os
            from pymongo import MongoClient
            
            mongodb_uri = os.getenv("MONGO_DB_URI", "mongodb+srv://jaydipmore74:xCpTm5OPAfRKYnif@cluster0.5jo18.mongodb.net/?retryWrites=true&w=majority")
            sync_client = MongoClient(mongodb_uri)
            sync_db = sync_client.youtube_api_db
            collection = sync_db.users
            
            cursor = collection.find({})
            users = list(cursor)
            sync_client.close()
            
            # Convert datetime objects to strings for template rendering
            for user in users:
                if 'created_at' in user and isinstance(user['created_at'], datetime):
                    user['created_at'] = user['created_at'].isoformat()
            
            logger.info(f"Retrieved {len(users)} users")
            return users
            
        except Exception as e:
            logger.error(f"Error retrieving users: {e}")
            return []
    
    @staticmethod
    def create_api_key(user_id: str, name: str, rate_limit: int = 1000, expires_days: int = 365) -> Optional[str]:
        """Create new API key with full professional features"""
        try:
            # Create synchronous MongoDB client directly
            import os
            from pymongo import MongoClient
            
            mongodb_uri = os.getenv("MONGO_DB_URI", "mongodb+srv://jaydipmore74:xCpTm5OPAfRKYnif@cluster0.5jo18.mongodb.net/?retryWrites=true&w=majority")
            sync_client = MongoClient(mongodb_uri)
            sync_db = sync_client.youtube_api_db
            api_keys_collection = sync_db.api_keys
            users_collection = sync_db.users
            
            # Check if user exists, create if not
            user = users_collection.find_one({'_id': user_id})
            if not user:
                new_user = User(username=f'user_{user_id[:8]}', email=f'user_{user_id[:8]}@example.com', _id=user_id)
                user_result = users_collection.insert_one(new_user.to_dict())
                if not user_result.inserted_id:
                    raise Exception("Failed to create user")
                logger.info(f"Created new user: {user_id}")
            
            # Create API key with expiry
            api_key = APIKey(user_id=user_id, name=name, rate_limit=rate_limit)
            
            # Add professional features
            key_data = api_key.to_dict()
            key_data.update({
                'expires_at': datetime.utcnow() + timedelta(days=expires_days),
                'last_used': None,
                'request_count': 0,
                'status': 'active',
                'permissions': ['read', 'download'],
                'created_by': 'admin',
                'notes': f'API key for {name}'
            })
            
            # Insert into database
            result = api_keys_collection.insert_one(key_data)
            
            if result.inserted_id:
                # Log successful creation
                logger.info(f"✓ API key created successfully: {api_key.key[:12]}... for user {user_id}")
                
                # Create usage tracking entry
                usage_collection = sync_db.api_key_usage
                usage_collection.insert_one({
                    'api_key_id': key_data['_id'],
                    'event': 'created',
                    'timestamp': datetime.utcnow(),
                    'details': f'API key {name} created for user {user_id}'
                })
                
                sync_client.close()
                return api_key.key
            else:
                sync_client.close()
                raise Exception("Database insert failed")
                
        except Exception as e:
            logger.error(f"❌ API key creation failed: {e}")
            if 'sync_client' in locals():
                sync_client.close()
            return None
    
    @staticmethod
    def toggle_api_key(key_id: str) -> bool:
        """Toggle API key status synchronously"""
        try:
            import os
            from pymongo import MongoClient
            
            mongodb_uri = os.getenv("MONGO_DB_URI", "mongodb+srv://jaydipmore74:xCpTm5OPAfRKYnif@cluster0.5jo18.mongodb.net/?retryWrites=true&w=majority")
            sync_client = MongoClient(mongodb_uri)
            sync_db = sync_client.youtube_api_db
            collection = sync_db.api_keys
            
            key_data = collection.find_one({'_id': key_id})
            if key_data:
                new_status = not key_data.get('is_active', True)
                result = collection.update_one(
                    {'_id': key_id},
                    {'$set': {'is_active': new_status}}
                )
                sync_client.close()
                if result.modified_count > 0:
                    logger.info(f"Toggled API key {key_id} to {'active' if new_status else 'inactive'}")
                    return True
            else:
                sync_client.close()
            return False
            
        except Exception as e:
            logger.error(f"Error toggling API key: {e}")
            return False
    
    @staticmethod
    def delete_api_key(key_id: str) -> bool:
        """Delete API key synchronously"""
        try:
            import os
            from pymongo import MongoClient
            
            mongodb_uri = os.getenv("MONGO_DB_URI", "mongodb+srv://jaydipmore74:xCpTm5OPAfRKYnif@cluster0.5jo18.mongodb.net/?retryWrites=true&w=majority")
            sync_client = MongoClient(mongodb_uri)
            sync_db = sync_client.youtube_api_db
            collection = sync_db.api_keys
            
            result = collection.delete_one({'_id': key_id})
            sync_client.close()
            
            if result.deleted_count > 0:
                logger.info(f"Deleted API key: {key_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting API key: {e}")
            return False

# Global instance
sync_db = SyncDatabase()