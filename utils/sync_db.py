"""
Synchronous database operations helper
Professional-grade MongoDB operations for admin panel
"""

import logging
from pymongo.errors import PyMongoError
from database.simple_mongo import get_api_keys_collection, get_users_collection
from models_simple import User, APIKey
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class SyncDatabase:
    """Synchronous database operations for admin panel"""
    
    @staticmethod
    def get_all_api_keys() -> List[Dict[str, Any]]:
        """Get all API keys synchronously"""
        try:
            collection = get_api_keys_collection()
            if collection is None:
                logger.error("API keys collection not available")
                return []
            
            # Use synchronous find operation
            cursor = collection.find({})
            api_keys = list(cursor)
            
            # Convert datetime objects to strings for template rendering
            for key in api_keys:
                if 'created_at' in key and isinstance(key['created_at'], datetime):
                    key['created_at'] = key['created_at'].isoformat()
            
            logger.info(f"Retrieved {len(api_keys)} API keys")
            return api_keys
            
        except Exception as e:
            logger.error(f"Error retrieving API keys: {e}")
            return []
    
    @staticmethod
    def get_all_users() -> List[Dict[str, Any]]:
        """Get all users synchronously"""
        try:
            collection = get_users_collection()
            if collection is None:
                logger.error("Users collection not available")
                return []
            
            cursor = collection.find({})
            users = list(cursor)
            
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
    def create_api_key(user_id: str, name: str, rate_limit: int = 1000) -> Optional[str]:
        """Create new API key synchronously"""
        try:
            api_keys_collection = get_api_keys_collection()
            users_collection = get_users_collection()
            
            if not api_keys_collection or not users_collection:
                raise Exception("Database collections not available")
            
            # Check if user exists
            user = users_collection.find_one({'_id': user_id})
            if not user:
                # Create new user
                new_user = User(username=f'user_{user_id[:8]}', email=f'user_{user_id[:8]}@example.com', _id=user_id)
                users_collection.insert_one(new_user.to_dict())
                logger.info(f"Created new user: {user_id}")
            
            # Create API key
            api_key = APIKey(user_id=user_id, name=name, rate_limit=rate_limit)
            result = api_keys_collection.insert_one(api_key.to_dict())
            
            if result.inserted_id:
                logger.info(f"Created API key: {api_key.key[:12]}...")
                return api_key.key
            else:
                raise Exception("Failed to insert API key")
                
        except Exception as e:
            logger.error(f"Error creating API key: {e}")
            return None
    
    @staticmethod
    def toggle_api_key(key_id: str) -> bool:
        """Toggle API key status synchronously"""
        try:
            collection = get_api_keys_collection()
            if not collection:
                raise Exception("API keys collection not available")
            
            key_data = collection.find_one({'_id': key_id})
            if key_data:
                new_status = not key_data.get('is_active', True)
                result = collection.update_one(
                    {'_id': key_id},
                    {'$set': {'is_active': new_status}}
                )
                if result.modified_count > 0:
                    logger.info(f"Toggled API key {key_id} to {'active' if new_status else 'inactive'}")
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Error toggling API key: {e}")
            return False
    
    @staticmethod
    def delete_api_key(key_id: str) -> bool:
        """Delete API key synchronously"""
        try:
            collection = get_api_keys_collection()
            if not collection:
                raise Exception("API keys collection not available")
            
            result = collection.delete_one({'_id': key_id})
            if result.deleted_count > 0:
                logger.info(f"Deleted API key: {key_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting API key: {e}")
            return False

# Global instance
sync_db = SyncDatabase()