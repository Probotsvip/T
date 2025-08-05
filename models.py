from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

class User:
    def __init__(self, username: str, email: str, password: str = None, _id: str = None):
        self._id = _id or str(uuid.uuid4())
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password) if password else None
        self.created_at = datetime.utcnow()
        self.is_active = True
        self.is_admin = False
        
    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            '_id': self._id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'created_at': self.created_at,
            'is_active': self.is_active,
            'is_admin': self.is_admin
        }

class APIKey:
    def __init__(self, user_id: str, name: str, _id: str = None):
        self._id = _id or str(uuid.uuid4())
        self.user_id = user_id
        self.name = name
        self.key = self.generate_key()
        self.created_at = datetime.utcnow()
        self.is_active = True
        self.rate_limit = 1000  # requests per hour
        self.usage_count = 0
        self.last_used = None
        
    @staticmethod
    def generate_key() -> str:
        return f"yt_api_{uuid.uuid4().hex}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            '_id': self._id,
            'user_id': self.user_id,
            'name': self.name,
            'key': self.key,
            'created_at': self.created_at,
            'is_active': self.is_active,
            'rate_limit': self.rate_limit,
            'usage_count': self.usage_count,
            'last_used': self.last_used
        }

class ContentCache:
    def __init__(self, youtube_id: str, title: str, duration: str, 
                 telegram_file_id: str, file_type: str, quality: str = None, _id: str = None):
        self._id = _id or str(uuid.uuid4())
        self.youtube_id = youtube_id
        self.title = title
        self.duration = duration
        self.telegram_file_id = telegram_file_id
        self.file_type = file_type  # 'audio' or 'video'
        self.quality = quality
        self.created_at = datetime.utcnow()
        self.access_count = 0
        self.last_accessed = None
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            '_id': self._id,
            'youtube_id': self.youtube_id,
            'title': self.title,
            'duration': self.duration,
            'telegram_file_id': self.telegram_file_id,
            'file_type': self.file_type,
            'quality': self.quality,
            'created_at': self.created_at,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed
        }

class UsageStats:
    def __init__(self, api_key: str, endpoint: str, youtube_id: str = None, _id: str = None):
        self._id = _id or str(uuid.uuid4())
        self.api_key = api_key
        self.endpoint = endpoint
        self.youtube_id = youtube_id
        self.timestamp = datetime.utcnow()
        self.response_time = None
        self.status = None
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            '_id': self._id,
            'api_key': self.api_key,
            'endpoint': self.endpoint,
            'youtube_id': self.youtube_id,
            'timestamp': self.timestamp,
            'response_time': self.response_time,
            'status': self.status
        }

class ConcurrentUser:
    def __init__(self, session_id: str, api_key: str, endpoint: str, _id: str = None):
        self._id = _id or str(uuid.uuid4())
        self.session_id = session_id
        self.api_key = api_key
        self.endpoint = endpoint
        self.connected_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            '_id': self._id,
            'session_id': self.session_id,
            'api_key': self.api_key,
            'endpoint': self.endpoint,
            'connected_at': self.connected_at,
            'last_activity': self.last_activity
        }
