#!/usr/bin/env python3
"""
Rate limiting service with daily request resets at midnight
"""
import os
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any
from pymongo import MongoClient
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter with daily request tracking that resets at midnight"""
    
    def __init__(self):
        self.mongo_uri = os.getenv("MONGO_DB_URI", "mongodb+srv://jaydipmore74:xCpTm5OPAfRKYnif@cluster0.5jo18.mongodb.net/?retryWrites=true&w=majority")
    
    def check_and_update_daily_limit(self, api_key: str) -> Dict[str, Any]:
        """
        Check if API key can make request and update daily count
        Returns: {
            'allowed': bool,
            'daily_requests': int,
            'daily_limit': int,
            'remaining': int,
            'reset_at': str
        }
        """
        try:
            client = MongoClient(self.mongo_uri)
            db = client.youtube_api_db
            
            # Find API key
            key_data = db.api_keys.find_one({'key': api_key, 'is_active': True})
            if not key_data:
                client.close()
                return {
                    'allowed': False,
                    'daily_requests': 0,
                    'daily_limit': 0,
                    'remaining': 0,
                    'reset_at': 'Invalid API key',
                    'error': 'API key not found or inactive'
                }
            
            current_date = datetime.utcnow().date()
            current_date_str = current_date.isoformat()
            
            # Check if we need to reset daily counter (new day)
            last_reset_date = key_data.get('last_reset_date', current_date_str)
            daily_requests = key_data.get('daily_requests', 0)
            daily_limit = key_data.get('daily_limit', key_data.get('rate_limit', 1000))
            
            # Reset counter if it's a new day
            if last_reset_date != current_date_str:
                daily_requests = 0
                logger.info(f"Resetting daily counter for API key {api_key[:10]}... (new day)")
            
            # Check if limit exceeded
            if daily_requests >= daily_limit:
                client.close()
                next_reset = datetime.combine(current_date, datetime.min.time()).replace(hour=0, minute=0, second=0) + timedelta(days=1)
                return {
                    'allowed': False,
                    'daily_requests': daily_requests,
                    'daily_limit': daily_limit,
                    'remaining': 0,
                    'reset_at': next_reset.isoformat(),
                    'error': 'Daily limit exceeded'
                }
            
            # Increment request count
            new_daily_requests = daily_requests + 1
            
            # Update database
            update_result = db.api_keys.update_one(
                {'key': api_key},
                {
                    '$set': {
                        'daily_requests': new_daily_requests,
                        'daily_limit': daily_limit,
                        'last_reset_date': current_date_str,
                        'last_request_time': datetime.utcnow()
                    },
                    '$inc': {'usage_count': 1}
                }
            )
            
            client.close()
            
            if update_result.modified_count > 0:
                next_reset = datetime.combine(current_date, datetime.min.time()).replace(hour=0, minute=0, second=0) + timedelta(days=1)
                remaining = max(0, daily_limit - new_daily_requests)
                
                logger.info(f"API key {api_key[:10]}... used: {new_daily_requests}/{daily_limit}, remaining: {remaining}")
                
                return {
                    'allowed': True,
                    'daily_requests': new_daily_requests,
                    'daily_limit': daily_limit,
                    'remaining': remaining,
                    'reset_at': next_reset.isoformat()
                }
            else:
                return {
                    'allowed': False,
                    'daily_requests': daily_requests,
                    'daily_limit': daily_limit,
                    'remaining': max(0, daily_limit - daily_requests),
                    'reset_at': datetime.combine(current_date, datetime.min.time()).replace(hour=0, minute=0, second=0) + timedelta(days=1),
                    'error': 'Failed to update request count'
                }
                
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            return {
                'allowed': False,
                'daily_requests': 0,
                'daily_limit': 0,
                'remaining': 0,
                'reset_at': 'Error',
                'error': str(e)
            }
    
    def get_api_key_stats(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Get current stats for an API key"""
        try:
            client = MongoClient(self.mongo_uri)
            db = client.youtube_api_db
            
            key_data = db.api_keys.find_one({'key': api_key})
            client.close()
            
            if not key_data:
                return None
            
            current_date = datetime.utcnow().date().isoformat()
            last_reset_date = key_data.get('last_reset_date', current_date)
            daily_requests = key_data.get('daily_requests', 0) if last_reset_date == current_date else 0
            daily_limit = key_data.get('daily_limit', key_data.get('rate_limit', 1000))
            
            return {
                'key_name': key_data.get('name', 'Unknown'),
                'daily_requests': daily_requests,
                'daily_limit': daily_limit,
                'remaining': max(0, daily_limit - daily_requests),
                'total_usage': key_data.get('usage_count', 0),
                'is_active': key_data.get('is_active', True),
                'created_at': key_data.get('created_at'),
                'last_request_time': key_data.get('last_request_time'),
                'reset_at': datetime.combine(datetime.utcnow().date(), datetime.min.time()).replace(hour=0, minute=0, second=0) + timedelta(days=1)
            }
            
        except Exception as e:
            logger.error(f"Error getting API key stats: {e}")
            return None

# Global rate limiter instance
rate_limiter = RateLimiter()