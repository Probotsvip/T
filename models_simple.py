from datetime import datetime
from typing import Optional, Dict, Any

class User:
    def __init__(self, username: str, email: str, password_hash: str, api_key: str = None):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.api_key = api_key
        self.created_at = datetime.utcnow()
        self.is_active = True

class APIKey:
    def __init__(self, key: str, user_id: str, rate_limit: int = 1000):
        self.key = key
        self.user_id = user_id
        self.rate_limit = rate_limit
        self.created_at = datetime.utcnow()
        self.is_active = True
        self.usage_count = 0

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