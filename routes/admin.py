from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
import asyncio
from datetime import datetime
import uuid
from database.mongo import get_users_collection, get_api_keys_collection
from models import User, APIKey
from services.api_service import api_service
from config import ADMIN_USERNAME, ADMIN_PASSWORD
from utils.logging import LOGGER

logger = LOGGER(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def run_async(coro):
    """Helper to run async functions in Flask routes"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
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
    """Admin dashboard with analytics"""
    try:
        # Get analytics data
        analytics = run_async(api_service.get_analytics_data(24))
        
        # Get real-time concurrent users
        concurrent_users = run_async(api_service.get_concurrent_user_count())
        
        return render_template('admin/dashboard.html', 
                             analytics=analytics, 
                             concurrent_users=concurrent_users)
        
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
        return jsonify({'status': False, 'error': str(e)}), 500

@admin_bp.route('/cache/cleanup', methods=['POST'])
@admin_required
def cleanup_cache():
    """Cleanup old cache entries"""
    try:
        from services.telegram_cache import telegram_cache
        days = int(request.form.get('days', 30))
        
        run_async(telegram_cache.cleanup_old_cache(days))
        flash(f'Cache cleanup completed for entries older than {days} days', 'success')
        
    except Exception as e:
        logger.error(f"Cache cleanup error: {e}")
        flash('Error during cache cleanup', 'error')
    
    return redirect(url_for('admin.dashboard'))
