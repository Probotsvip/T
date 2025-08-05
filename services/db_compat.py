"""
Database compatibility layer for MongoDB-style operations using SQLAlchemy
"""
import uuid
from datetime import datetime
from database.db import db, User, APIKey, ContentCache, UsageStats, ConcurrentUser

class DatabaseCompat:
    """MongoDB-style database operations using SQLAlchemy"""
    
    @staticmethod
    def find_one(model, **kwargs):
        """Find one record"""
        return model.query.filter_by(**kwargs).first()
    
    @staticmethod
    def find(model, **kwargs):
        """Find multiple records"""
        return model.query.filter_by(**kwargs).all()
    
    @staticmethod
    def insert_one(model, data):
        """Insert one record"""
        # Convert MongoDB-style _id to id
        if '_id' in data:
            data['id'] = data.pop('_id')
        
        obj = model(**data)
        db.session.add(obj)
        db.session.commit()
        return obj
    
    @staticmethod
    def update_one(model, filter_dict, update_dict):
        """Update one record"""
        # Convert MongoDB-style _id to id
        if '_id' in filter_dict:
            filter_dict['id'] = filter_dict.pop('_id')
        
        record = model.query.filter_by(**filter_dict).first()
        if record:
            # Handle MongoDB-style $set and $inc operations
            if '$set' in update_dict:
                for key, value in update_dict['$set'].items():
                    if hasattr(record, key):
                        setattr(record, key, value)
            
            if '$inc' in update_dict:
                for key, value in update_dict['$inc'].items():
                    if hasattr(record, key):
                        current_value = getattr(record, key) or 0
                        setattr(record, key, current_value + value)
            
            # Handle direct updates
            for key, value in update_dict.items():
                if not key.startswith('$') and hasattr(record, key):
                    setattr(record, key, value)
            
            db.session.commit()
        return record
    
    @staticmethod
    def delete_one(model, **kwargs):
        """Delete one record"""
        # Convert MongoDB-style _id to id
        if '_id' in kwargs:
            kwargs['id'] = kwargs.pop('_id')
        
        record = model.query.filter_by(**kwargs).first()
        if record:
            db.session.delete(record)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def count_documents(model, **kwargs):
        """Count documents"""
        if not kwargs:
            return model.query.count()
        return model.query.filter_by(**kwargs).count()
    
    @staticmethod
    def delete_many(model, **kwargs):
        """Delete many records"""
        count = model.query.filter_by(**kwargs).count()
        model.query.filter_by(**kwargs).delete()
        db.session.commit()
        return count

# Global database instance
db_compat = DatabaseCompat()

# Collection-style accessors for compatibility
class Collections:
    @property
    def users(self):
        return User
    
    @property
    def api_keys(self):
        return APIKey
    
    @property
    def content_cache(self):
        return ContentCache
    
    @property
    def usage_stats(self):
        return UsageStats
    
    @property
    def concurrent_users(self):
        return ConcurrentUser

collections = Collections()

# Mock async functions for compatibility
async def async_find_one(model, **kwargs):
    return db_compat.find_one(model, **kwargs)

async def async_find(model, **kwargs):
    return db_compat.find(model, **kwargs)

async def async_insert_one(model, data):
    return db_compat.insert_one(model, data)

async def async_update_one(model, filter_dict, update_dict):
    return db_compat.update_one(model, filter_dict, update_dict)

async def async_delete_one(model, **kwargs):
    return db_compat.delete_one(model, **kwargs)

async def async_count_documents(model, **kwargs):
    return db_compat.count_documents(model, **kwargs)

async def async_delete_many(model, **kwargs):
    return db_compat.delete_many(model, **kwargs)