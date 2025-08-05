import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timedelta
import json

# Create database instance
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Database Models for YouTube API Server
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(50), primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    api_keys = db.relationship('APIKey', backref='owner', lazy=True, cascade='all, delete-orphan')

class APIKey(db.Model):
    __tablename__ = 'api_keys'
    
    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    key = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    rate_limit = db.Column(db.Integer, default=1000)
    usage_count = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)  # For automatic expiry

class ContentCache(db.Model):
    __tablename__ = 'content_cache'
    
    id = db.Column(db.String(50), primary_key=True)
    youtube_id = db.Column(db.String(100), nullable=False, index=True)
    title = db.Column(db.Text, nullable=False)
    duration = db.Column(db.String(20))
    telegram_file_id = db.Column(db.String(200), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)  # 'audio' or 'video'
    quality = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    access_count = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime)
    
    # Index for fast lookups
    __table_args__ = (
        db.Index('idx_youtube_file_type', 'youtube_id', 'file_type'),
        db.Index('idx_youtube_file_quality', 'youtube_id', 'file_type', 'quality'),
    )

class UsageStats(db.Model):
    __tablename__ = 'usage_stats'
    
    id = db.Column(db.String(50), primary_key=True)
    api_key = db.Column(db.String(100), nullable=False, index=True)
    endpoint = db.Column(db.String(100), nullable=False)
    youtube_id = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    response_time = db.Column(db.Float)
    status = db.Column(db.String(20), default='success')

class ConcurrentUser(db.Model):
    __tablename__ = 'concurrent_users'
    
    id = db.Column(db.String(50), primary_key=True)
    session_id = db.Column(db.String(100), nullable=False, unique=True)
    api_key = db.Column(db.String(100), nullable=False)
    endpoint = db.Column(db.String(100), nullable=False)
    connected_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)

# Database utility functions for compatibility with MongoDB-style operations
class DatabaseOperations:
    @staticmethod
    async def find_one(model, **kwargs):
        """Find one record asynchronously"""
        return model.query.filter_by(**kwargs).first()
    
    @staticmethod
    async def find(model, **kwargs):
        """Find multiple records asynchronously"""
        return model.query.filter_by(**kwargs).all()
    
    @staticmethod
    async def insert_one(model, data):
        """Insert one record asynchronously"""
        obj = model(**data)
        db.session.add(obj)
        db.session.commit()
        return obj
    
    @staticmethod
    async def update_one(model, filter_dict, update_dict):
        """Update one record asynchronously"""
        record = model.query.filter_by(**filter_dict).first()
        if record:
            for key, value in update_dict.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            db.session.commit()
        return record
    
    @staticmethod
    async def delete_one(model, **kwargs):
        """Delete one record asynchronously"""
        record = model.query.filter_by(**kwargs).first()
        if record:
            db.session.delete(record)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    async def count_documents(model, **kwargs):
        """Count documents asynchronously"""
        return model.query.filter_by(**kwargs).count()

# Compatibility functions for MongoDB-style operations
def get_users_collection():
    """Return User model for compatibility"""
    return User

def get_api_keys_collection():
    """Return APIKey model for compatibility"""
    return APIKey

def get_content_cache_collection():
    """Return ContentCache model for compatibility"""
    return ContentCache

def get_usage_stats_collection():
    """Return UsageStats model for compatibility"""
    return UsageStats

def get_concurrent_users_collection():
    """Return ConcurrentUser model for compatibility"""
    return ConcurrentUser

# Initialize database connection
async def init_db():
    """Initialize database tables"""
    try:
        # Create all tables
        db.create_all()
        
        # Create default admin user if not exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            from werkzeug.security import generate_password_hash
            admin_user = User(
                id='admin_user_1',
                username='admin',
                email='admin@youtubeapi.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin_user)
            
            # Create default API key for testing
            from models import APIKey as APIKeyModel
            default_api_key = APIKey(
                id='default_api_key_1',
                user_id='admin_user_1',
                name='Default Admin Key',
                key='yt_api_admin_default_key_10000_requests',
                rate_limit=10000
            )
            db.session.add(default_api_key)
            db.session.commit()
        
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

# Database utility class for async operations
class AsyncDB:
    """Async wrapper for database operations"""
    
    @staticmethod
    def run_sync(func):
        """Convert sync database operations to async"""
        import asyncio
        try:
            return func()
        except Exception as e:
            print(f"Database operation error: {e}")
            return None