"""
Professional YouTube API Database System
Custom synchronous operations for admin panel management
"""

import logging
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from models_simple import User, APIKey
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os
import uuid

logger = logging.getLogger(__name__)

class YouTubeAPIDatabase:
    """Professional database system for YouTube API server admin panel"""
    
    def __init__(self):
        self.mongodb_uri = os.getenv("MONGO_DB_URI", "mongodb+srv://jaydipmore74:xCpTm5OPAfRKYnif@cluster0.5jo18.mongodb.net/?retryWrites=true&w=majority")
        self.db_name = "youtube_api_db"
    
    def get_database_connection(self):
        """Get database connection and return database object"""
        try:
            client = MongoClient(self.mongodb_uri)
            db = client[self.db_name]
            return client, db
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None, None
    
    def get_all_api_keys(self) -> List[Dict[str, Any]]:
        """Get all API keys with professional formatting"""
        try:
            client, db = self.get_database_connection()
            if not db:
                return []
            
            # Get API keys with user information
            pipeline = [
                {
                    '$lookup': {
                        'from': 'users',
                        'localField': 'user_id',
                        'foreignField': '_id',
                        'as': 'user_info'
                    }
                },
                {'$unwind': {'path': '$user_info', 'preserveNullAndEmptyArrays': True}},
                {'$sort': {'created_at': -1}}
            ]
            
            api_keys = list(db.api_keys.aggregate(pipeline))
            client.close()
            
            # Professional formatting
            for key in api_keys:
                # Format dates
                if 'created_at' in key and isinstance(key['created_at'], datetime):
                    key['created_at_formatted'] = key['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                
                # Check expiry
                if 'expires_at' in key and key['expires_at']:
                    key['is_expired'] = datetime.utcnow() > key['expires_at']
                    key['expires_at_formatted'] = key['expires_at'].strftime('%Y-%m-%d')
                    # Calculate days until expiry
                    days_left = (key['expires_at'] - datetime.utcnow()).days
                    key['days_until_expiry'] = max(0, days_left)
                else:
                    key['is_expired'] = False
                    key['days_until_expiry'] = 365
                
                # Security preview
                if 'key' in key:
                    key['key_display'] = key['key'][:16] + '...'
                
                # User information
                if 'user_info' in key:
                    key['username'] = key['user_info'].get('username', 'Unknown')
                    key['user_email'] = key['user_info'].get('email', 'No email')
                else:
                    key['username'] = 'Unknown User'
                    key['user_email'] = 'No email'
                
                # Status indicators
                key['status_badge'] = 'success' if key.get('is_active', True) else 'danger'
                key['status_text'] = 'Active' if key.get('is_active', True) else 'Inactive'
            
            logger.info(f"Successfully loaded {len(api_keys)} API keys")
            return api_keys
            
        except Exception as e:
            logger.error(f"Failed to retrieve API keys: {e}")
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
    
    def create_api_key(self, user_id: str, name: str, rate_limit: int = 1000, expires_days: int = 365) -> Optional[str]:
        """Create API key with enterprise-grade features"""
        try:
            client, db = self.get_database_connection()
            if not db:
                raise Exception("Database connection failed")
            
            # Ensure user exists
            user = db.users.find_one({'_id': user_id})
            if not user:
                # Create user automatically
                new_user = User(
                    username=f'api_user_{user_id[:8]}', 
                    email=f'user_{user_id[:8]}@apiserver.com', 
                    _id=user_id
                )
                user_result = db.users.insert_one(new_user.to_dict())
                if not user_result.inserted_id:
                    client.close()
                    raise Exception("Failed to create user account")
                logger.info(f"Auto-created user account: {user_id}")
            
            # Generate API key with enterprise features
            api_key = APIKey(user_id=user_id, name=name, rate_limit=rate_limit)
            
            # Enterprise-grade key configuration
            key_data = api_key.to_dict()
            key_data.update({
                'expires_at': datetime.utcnow() + timedelta(days=expires_days),
                'last_used': None,
                'request_count': 0,
                'daily_usage': 0,
                'monthly_usage': 0,
                'status': 'active',
                'permissions': ['youtube_download', 'metadata_access', 'streaming'],
                'created_by': 'admin_panel',
                'notes': f'Enterprise API key for {name}',
                'ip_restrictions': [],
                'domain_whitelist': [],
                'usage_alerts': True,
                'auto_renewal': False,
                'tier': 'professional'
            })
            
            # Save to database
            result = db.api_keys.insert_one(key_data)
            
            if result.inserted_id:
                # Log creation event
                db.api_key_events.insert_one({
                    'api_key_id': key_data['_id'],
                    'event_type': 'created',
                    'timestamp': datetime.utcnow(),
                    'details': f'API key "{name}" created for user {user_id}',
                    'admin_action': True,
                    'ip_address': None
                })
                
                # Initialize usage tracking
                db.api_key_usage.insert_one({
                    'api_key_id': key_data['_id'],
                    'date': datetime.utcnow().strftime('%Y-%m-%d'),
                    'requests': 0,
                    'bandwidth_mb': 0,
                    'errors': 0,
                    'created_at': datetime.utcnow()
                })
                
                client.close()
                logger.info(f"✅ API key created: {api_key.key[:16]}... | User: {user_id} | Rate: {rate_limit}/hr")
                return api_key.key
            
            client.close()
            raise Exception("Database insertion failed")
                
        except Exception as e:
            logger.error(f"❌ API key creation error: {e}")
            return None
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users with API key statistics"""
        try:
            client, db = self.get_database_connection()
            if not db:
                return []
            
            # Get users with their API key counts
            pipeline = [
                {
                    '$lookup': {
                        'from': 'api_keys',
                        'localField': '_id',
                        'foreignField': 'user_id',
                        'as': 'api_keys'
                    }
                },
                {
                    '$addFields': {
                        'api_key_count': {'$size': '$api_keys'},
                        'active_keys': {
                            '$size': {
                                '$filter': {
                                    'input': '$api_keys',
                                    'cond': {'$eq': ['$$this.is_active', True]}
                                }
                            }
                        }
                    }
                },
                {'$sort': {'created_at': -1}}
            ]
            
            users = list(db.users.aggregate(pipeline))
            client.close()
            
            # Format user data
            for user in users:
                if 'created_at' in user and isinstance(user['created_at'], datetime):
                    user['created_at_formatted'] = user['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                
                # User status
                user['status'] = 'Active' if user.get('api_key_count', 0) > 0 else 'Inactive'
                user['status_badge'] = 'success' if user.get('api_key_count', 0) > 0 else 'secondary'
                
                # Remove sensitive API key data
                if 'api_keys' in user:
                    del user['api_keys']
            
            logger.info(f"Successfully loaded {len(users)} users")
            return users
            
        except Exception as e:
            logger.error(f"Failed to retrieve users: {e}")
            return []
    
    def toggle_api_key(self, key_id: str) -> bool:
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

# Global database instance
youtube_api_db = YouTubeAPIDatabase()