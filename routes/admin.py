from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
import asyncio
from datetime import datetime, timedelta
import uuid
import time
from typing import Dict, Any, Optional
from database.simple_mongo import (
    get_users_collection, get_api_keys_collection, 
    get_usage_stats_collection, get_concurrent_users_collection,
    get_content_cache_collection
)
from models_simple import User, APIKey
from services.api_service import api_service
from services.telegram_cache import TelegramCache

# Initialize the full Telegram cache system  
telegram_cache = TelegramCache()
from config import ADMIN_USERNAME, ADMIN_PASSWORD
from utils.logging import LOGGER

logger = LOGGER(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

class ProfessionalAdminService:
    """Professional admin service with comprehensive features"""
    
    def __init__(self):
        self.cache_stats = {}
        self.performance_metrics = {}
        self.last_cache_update = 0
    
    async def get_comprehensive_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive analytics data for professional dashboard"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # Parallel data collection for optimal performance
            analytics_tasks = [
                self._get_usage_analytics(start_time, end_time),
                self._get_cache_analytics(),
                self._get_system_performance(),
                self._get_api_key_stats(),
                self._get_concurrent_user_analytics()
            ]
            
            results = await asyncio.gather(*analytics_tasks, return_exceptions=True)
            
            return {
                'usage_stats': results[0] if not isinstance(results[0], Exception) else {},
                'cache_stats': results[1] if not isinstance(results[1], Exception) else {},
                'performance': results[2] if not isinstance(results[2], Exception) else {},
                'api_keys': results[3] if not isinstance(results[3], Exception) else {},
                'concurrent_users': results[4] if not isinstance(results[4], Exception) else {},
                'period_hours': hours,
                'generated_at': end_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Comprehensive analytics failed: {e}")
            return self._get_fallback_analytics()
    
    async def _get_usage_analytics(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get detailed usage analytics"""
        usage_collection = get_usage_stats_collection()
        
        # Query for usage data in time range
        usage_query = {
            'timestamp': {
                '$gte': start_time,
                '$lte': end_time
            }
        }
        
        # Aggregate usage statistics
        pipeline = [
            {'$match': usage_query},
            {'$group': {
                '_id': '$endpoint',
                'count': {'$sum': 1},
                'unique_ips': {'$addToSet': '$ip'},
                'avg_response_time': {'$avg': '$response_time'}
            }},
            {'$sort': {'count': -1}}
        ]
        
        usage_data = []
        total_requests = 0
        if usage_collection is not None:
            async for doc in usage_collection.aggregate(pipeline):
                usage_data.append({
                    'endpoint': doc['_id'],
                    'requests': doc['count'],
                    'unique_users': len(doc['unique_ips']),
                    'avg_response_time': round(doc.get('avg_response_time', 0), 2)
                })
            
            # Get total requests
            total_requests = await usage_collection.count_documents(usage_query)
        
        return {
            'total_requests': total_requests,
            'endpoints': usage_data,
            'period_start': start_time.isoformat(),
            'period_end': end_time.isoformat()
        }
    
    async def _get_cache_analytics(self) -> Dict[str, Any]:
        """Get comprehensive cache analytics"""
        cache_collection = get_content_cache_collection()
        
        # Cache statistics pipeline
        pipeline = [
            {'$group': {
                '_id': '$status',
                'count': {'$sum': 1},
                'total_size': {'$sum': '$file_size'},
                'avg_access_count': {'$avg': '$access_count'}
            }}
        ]
        
        cache_stats = {}
        total_cached = 0
        total_size = 0
        
        if cache_collection is not None:
            async for doc in cache_collection.aggregate(pipeline):
                status = doc['_id'] or 'unknown'
                cache_stats[status] = {
                    'count': doc['count'],
                    'total_size_mb': round(doc.get('total_size', 0) / (1024*1024), 2),
                    'avg_access_count': round(doc.get('avg_access_count', 0), 1)
                }
                total_cached += doc['count']
                total_size += doc.get('total_size', 0)
        
        async for doc in cache_collection.aggregate(pipeline):
            status = doc['_id']
            count = doc['count']
            size = doc.get('total_size', 0)
            
            cache_stats[status] = {
                'count': count,
                'size_mb': round(size / (1024 * 1024), 2) if size else 0,
                'avg_access': round(doc.get('avg_access_count', 0), 1)
            }
            
            total_cached += count
            total_size += size
        
        # Get cache hit rate (simplified calculation)
        active_cache = cache_stats.get('active', {}).get('count', 0)
        cache_hit_rate = round((active_cache / total_cached * 100), 1) if total_cached > 0 else 0
        
        return {
            'total_cached_items': total_cached,
            'total_cache_size_mb': round(total_size / (1024 * 1024), 2),
            'cache_hit_rate_percent': cache_hit_rate,
            'by_status': cache_stats,
            'telegram_bot_active': telegram_cache.bot is not None
        }
    
    async def _get_system_performance(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            # MongoDB connection stats
            db_stats = await mongodb.get_connection_stats()
            
            # Server uptime and health
            current_time = time.time()
            
            return {
                'database': {
                    'connection_pool_ready': db_stats.get('connection_pool_ready', False),
                    'active_connections': db_stats.get('connections_active', 0),
                    'available_connections': db_stats.get('connections_available', 0),
                    'uptime_seconds': db_stats.get('uptime_seconds', 0)
                },
                'server': {
                    'status': 'operational',
                    'timestamp': current_time,
                    'response_time_ms': 0  # Will be measured by frontend
                },
                'telegram_cache': {
                    'status': 'active' if telegram_cache.bot else 'inactive',
                    'upload_semaphore_available': getattr(telegram_cache, 'upload_semaphore', None) is not None
                }
            }
            
        except Exception as e:
            logger.error(f"Performance metrics failed: {e}")
            return {'error': str(e)}
    
    async def _get_api_key_stats(self) -> Dict[str, Any]:
        """Get API key statistics"""
        api_keys_collection = get_api_keys_collection()
        
        # Count active vs inactive keys
        if api_keys_collection is not None:
            active_keys = await api_keys_collection.count_documents({'is_active': True})
            inactive_keys = await api_keys_collection.count_documents({'is_active': False})
        else:
            active_keys = 0
            inactive_keys = 0
        
        # Get usage distribution
        top_keys = []
        if api_keys_collection is not None:
            pipeline = [
                {'$match': {'is_active': True}},
                {'$sort': {'usage_count': -1}},
                {'$limit': 10},
                {'$project': {
                    'key': {'$substr': ['$key', 0, 8]},
                    'usage_count': 1,
                    'rate_limit': 1,
                    'created_at': 1
                }}
            ]
            
            async for doc in api_keys_collection.aggregate(pipeline):
                top_keys.append({
                    'key_preview': doc['key'] + '...',
                    'usage_count': doc.get('usage_count', 0),
                    'rate_limit': doc.get('rate_limit', 1000),
                    'created_at': doc.get('created_at', '')
                })
        
        return {
            'active_keys': active_keys,
            'inactive_keys': inactive_keys,
            'total_keys': active_keys + inactive_keys,
            'top_usage_keys': top_keys
        }
    
    async def _get_concurrent_user_analytics(self) -> Dict[str, Any]:
        """Get concurrent user analytics"""
        concurrent_collection = get_concurrent_users_collection()
        
        # Current active users (last 5 minutes)
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        if concurrent_collection is not None:
            active_users = await concurrent_collection.count_documents({
                'last_activity': {'$gte': five_minutes_ago}
            })
        else:
            active_users = 0
        
        # Peak users in last 24 hours
        peak_users = 0
        if concurrent_collection is not None:
            pipeline = [
                {'$group': {
                    '_id': {
                        'hour': {'$hour': '$last_activity'},
                        'date': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$last_activity'}}
                    },
                    'count': {'$sum': 1}
                }},
                {'$sort': {'count': -1}},
                {'$limit': 1}
            ]
            
            async for doc in concurrent_collection.aggregate(pipeline):
                peak_users = doc['count']
                break
        
        return {
            'current_active_users': active_users,
            'peak_users_24h': peak_users,
            'capacity_utilization_percent': round((active_users / 10000) * 100, 2)
        }
    
    def _get_fallback_analytics(self) -> Dict[str, Any]:
        """Fallback analytics when database is unavailable"""
        return {
            'usage_stats': {'total_requests': 0, 'endpoints': []},
            'cache_stats': {'total_cached_items': 0, 'cache_hit_rate_percent': 0},
            'performance': {'database': {'status': 'unavailable'}},
            'api_keys': {'active_keys': 0, 'total_keys': 0},
            'concurrent_users': {'current_active_users': 0},
            'status': 'fallback_mode'
        }

# Professional admin service instance
admin_service = ProfessionalAdminService()

def run_async(coro):
    """Professional async helper with error handling"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    except Exception as e:
        logger.error(f"Async operation failed: {e}")
        return None
    finally:
        loop.close()

def admin_required(f):
    """Decorator to require admin authentication"""
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Successfully logged in!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Successfully logged out!', 'success')
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Professional admin dashboard with comprehensive analytics"""
    try:
        # Get comprehensive professional analytics
        analytics = run_async(admin_service.get_comprehensive_analytics(24))
        
        if not analytics:
            analytics = admin_service._get_fallback_analytics()
        
        # Professional dashboard data
        dashboard_data = {
            'analytics': analytics,
            'concurrent_users': analytics.get('concurrent_users', {}).get('current_active_users', 0),
            'system_status': 'operational',
            'professional_features': {
                'cache_enabled': True,
                'telegram_integration': True,
                'real_time_analytics': True,
                'performance_monitoring': True
            }
        }
        
        return render_template('admin/dashboard.html', **dashboard_data)
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        flash('Error loading dashboard data', 'error')
        return render_template('admin/dashboard.html', analytics={}, concurrent_users=0)

@admin_bp.route('/api-keys')
@admin_required
def api_keys():
    """Manage API keys"""
    try:
        api_keys_collection = get_api_keys_collection()
        users_collection = get_users_collection()
        
        # Get all API keys with user info
        pipeline = [
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'user_id',
                    'foreignField': '_id',
                    'as': 'user'
                }
            },
            {'$unwind': {'path': '$user', 'preserveNullAndEmptyArrays': True}},
            {'$sort': {'created_at': -1}}
        ]
        
        api_keys_data = run_async(api_keys_collection.aggregate(pipeline).to_list(None))
        users_data = run_async(users_collection.find({}).to_list(None))
        
        return render_template('admin/api_keys.html', 
                             api_keys=api_keys_data, 
                             users=users_data)
        
    except Exception as e:
        logger.error(f"API keys page error: {e}")
        flash('Error loading API keys', 'error')
        return render_template('admin/api_keys.html', api_keys=[], users=[])

@admin_bp.route('/api-keys/create', methods=['POST'])
@admin_required
def create_api_key():
    """Create new API key"""
    try:
        user_id = request.form['user_id']
        key_name = request.form['name']
        rate_limit = int(request.form.get('rate_limit', 1000))
        
        # Create user if doesn't exist
        users_collection = get_users_collection()
        user = run_async(users_collection.find_one({'_id': user_id}))
        
        if not user:
            # Create new user
            username = request.form.get('username', f'user_{user_id[:8]}')
            email = request.form.get('email', f'{username}@example.com')
            
            new_user = User(username=username, email=email, _id=user_id)
            run_async(users_collection.insert_one(new_user.to_dict()))
        
        # Create API key
        api_key = APIKey(user_id=user_id, name=key_name)
        api_key.rate_limit = rate_limit
        
        api_keys_collection = get_api_keys_collection()
        run_async(api_keys_collection.insert_one(api_key.to_dict()))
        
        flash(f'API key created successfully: {api_key.key}', 'success')
        
    except Exception as e:
        logger.error(f"API key creation error: {e}")
        flash('Error creating API key', 'error')
    
    return redirect(url_for('admin.api_keys'))

@admin_bp.route('/api-keys/<key_id>/toggle', methods=['POST'])
@admin_required
def toggle_api_key(key_id):
    """Toggle API key active status"""
    try:
        api_keys_collection = get_api_keys_collection()
        
        key_data = run_async(api_keys_collection.find_one({'_id': key_id}))
        if key_data:
            new_status = not key_data.get('is_active', True)
            run_async(api_keys_collection.update_one(
                {'_id': key_id},
                {'$set': {'is_active': new_status}}
            ))
            
            status_text = 'activated' if new_status else 'deactivated'
            flash(f'API key {status_text} successfully', 'success')
        else:
            flash('API key not found', 'error')
            
    except Exception as e:
        logger.error(f"API key toggle error: {e}")
        flash('Error updating API key', 'error')
    
    return redirect(url_for('admin.api_keys'))

@admin_bp.route('/api-keys/<key_id>/delete', methods=['POST'])
@admin_required
def delete_api_key(key_id):
    """Delete API key"""
    try:
        api_keys_collection = get_api_keys_collection()
        result = run_async(api_keys_collection.delete_one({'_id': key_id}))
        
        if result.deleted_count > 0:
            flash('API key deleted successfully', 'success')
        else:
            flash('API key not found', 'error')
            
    except Exception as e:
        logger.error(f"API key deletion error: {e}")
        flash('Error deleting API key', 'error')
    
    return redirect(url_for('admin.api_keys'))

@admin_bp.route('/analytics')
@admin_required
def analytics():
    """Detailed analytics page"""
    try:
        hours = int(request.args.get('hours', 24))
        analytics_data = run_async(api_service.get_analytics_data(hours))
        
        return render_template('admin/analytics.html', 
                             analytics=analytics_data, 
                             hours=hours)
        
    except Exception as e:
        logger.error(f"Analytics page error: {e}")
        flash('Error loading analytics', 'error')
        return render_template('admin/analytics.html', analytics={}, hours=24)

@admin_bp.route('/api/stats')
@admin_required  
def api_stats():
    """API endpoint for real-time stats (for AJAX)"""
    try:
        # Real MongoDB Atlas stats
        concurrent_users = run_async(api_service.get_concurrent_user_count())
        analytics = run_async(api_service.get_analytics_data(1))  # Last hour
        
        return jsonify({
            'status': True,
            'concurrent_users': concurrent_users,
            'hourly_requests': analytics.get('total_requests', 0),
            'cache_hit_rate': analytics.get('cache_hit_rate', 0),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"API stats error: {e}")
        return jsonify({
            'status': True,
            'concurrent_users': 0,
            'hourly_requests': 0,
            'cache_hit_rate': 0,
            'timestamp': datetime.utcnow().isoformat()
        })

@admin_bp.route('/cache/cleanup', methods=['POST'])
@admin_required
def cleanup_cache():
    """Cleanup old cache entries"""
    try:
        # Use the already imported telegram_cache
        days = int(request.form.get('days', 30))
        
        run_async(telegram_cache.cleanup_old_cache(days))
        flash(f'Cache cleanup completed for entries older than {days} days', 'success')
        
    except Exception as e:
        logger.error(f"Cache cleanup error: {e}")
        flash('Error during cache cleanup', 'error')
    
    return redirect(url_for('admin.dashboard'))
