from datetime import datetime
from typing import Optional, Dict, Any
import secrets
import uuid

class User:
    def __init__(self, username: str, email: str, password_hash: str = None, _id: str = None):
        self._id = _id or str(uuid.uuid4())
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = datetime.utcnow()
        self.is_active = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            '_id': self._id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'created_at': self.created_at,
            'is_active': self.is_active
        }

class APIKey:
    def __init__(self, user_id: str, name: str = None, key: str = None, rate_limit: int = 1000):
        self._id = str(uuid.uuid4())
        self.key = key or self._generate_api_key()
        self.user_id = user_id
        self.name = name or f"API Key {self.key[:8]}"
        self.rate_limit = rate_limit
        self.created_at = datetime.utcnow()
        self.is_active = True
        self.usage_count = 0
    
    def _generate_api_key(self) -> str:
        """Generate a secure API key"""
        return 'sk-' + secrets.token_urlsafe(48)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            '_id': self._id,
            'key': self.key,
            'user_id': self.user_id,
            'name': self.name,
            'rate_limit': self.rate_limit,
            'created_at': self.created_at,
            'is_active': self.is_active,
            'usage_count': self.usage_count
        }

class ContentCache:
    def __init__(self, youtube_id: str, file_type: str, telegram_file_id: str, 
                 quality: str = None, title: str = None):
        self.youtube_id = youtube_id
        self.file_type = file_type  # 'video' or 'audio'
        self.telegram_file_id = telegram_file_id
        self.quality = quality
        self.title = title
        self.cached_at = datetime.utcnow()
        self.status = 'active'
        self.file_size = 0
        self.duration = 0

class UsageStats:
    def __init__(self, api_key: str, endpoint: str, status: str = 'success'):
        self.api_key = api_key
        self.endpoint = endpoint
        self.status = status
        self.timestamp = datetime.utcnow()
        self.response_time = 0

class ConcurrentUser:
    def __init__(self, session_id: str, api_key: str = None):
        self.session_id = session_id
        self.api_key = api_key
        self.last_activity = datetime.utcnow()
        self.status = 'active'