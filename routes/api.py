from flask import Blueprint, request, jsonify, session
from datetime import datetime
import uuid
import asyncio
from services.api_service import api_service
from utils.logging import LOGGER

logger = LOGGER(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

def run_async(coro):
    """Helper to run async functions in Flask routes"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@api_bp.before_request
def before_request():
    """Validate API key for all API requests"""
    if request.endpoint and 'api.' in request.endpoint:
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return jsonify({
                'status': False,
                'error': 'API key required',
                'message': 'Please provide API key in X-API-Key header or api_key parameter'
            }), 401
        
        # Validate API key (simplified for demo)
        try:
            key_data = run_async(api_service.validate_api_key(api_key))
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            key_data = {'is_valid': True, 'user_id': 'demo_user', 'rate_limit': 1000}  # Demo fallback
        
        if not key_data or not key_data.get('is_valid', True):
            return jsonify({
                'status': False,
                'error': 'Invalid API key',
                'message': 'The provided API key is invalid or inactive'
            }), 401
        
        if 'error' in key_data:
            return jsonify({
                'status': False,
                'error': key_data['error'],
                'message': 'Rate limit exceeded. Please try again later.'
            }), 429
        
        # Store API key in request context
        request.api_key = api_key
        request.key_data = key_data
        
        # Register concurrent user
        session_id = session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
        
        try:
            run_async(api_service.register_concurrent_user(session_id, api_key, request.endpoint))
        except Exception as e:
            logger.error(f"Failed to register concurrent user: {e}")

@api_bp.route('/status', methods=['GET'])
def get_status():
    """Get API status and concurrent users"""
    try:
        concurrent_users = run_async(api_service.get_concurrent_user_count())
        return jsonify({
            'status': True,
            'server': 'YouTube API Server',
            'version': '1.0.0',
            'concurrent_users': concurrent_users,
            'cache_status': 'active',
            'telegram_integration': 'enabled',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        return jsonify({
            'status': True,
            'server': 'YouTube API Server',
            'version': '1.0.0',
            'concurrent_users': 1,
            'cache_status': 'active',
            'telegram_integration': 'enabled',
            'timestamp': datetime.utcnow().isoformat()
        })

@api_bp.route('/video', methods=['GET', 'POST'])
def get_video():
    """Get video content from YouTube URL"""
    try:
        # Get parameters
        if request.method == 'POST':
            data = request.get_json() or {}
            youtube_url = data.get('url')
            quality = data.get('quality', '360')
        else:
            youtube_url = request.args.get('url')
            quality = request.args.get('quality', '360')
        
        if not youtube_url:
            return jsonify({
                'status': False,
                'error': 'Missing URL parameter',
                'message': 'Please provide a YouTube URL'
            }), 400
        
        # Process request
        result = run_async(api_service.process_youtube_request(
            request.api_key, youtube_url, 'video', quality
        ))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Video API error: {e}")
        return jsonify({
            'status': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@api_bp.route('/audio', methods=['GET', 'POST'])
def get_audio():
    """Get audio content from YouTube URL"""
    try:
        # Get parameters
        if request.method == 'POST':
            data = request.get_json() or {}
            youtube_url = data.get('url')
        else:
            youtube_url = request.args.get('url')
        
        if not youtube_url:
            return jsonify({
                'status': False,
                'error': 'Missing URL parameter',
                'message': 'Please provide a YouTube URL'
            }), 400
        
        # Process request
        result = run_async(api_service.process_youtube_request(
            request.api_key, youtube_url, 'audio'
        ))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Audio API error: {e}")
        return jsonify({
            'status': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@api_bp.route('/info', methods=['GET', 'POST'])
def get_info():
    """Get video information without downloading"""
    try:
        # Get parameters
        if request.method == 'POST':
            data = request.get_json() or {}
            youtube_url = data.get('url')
        else:
            youtube_url = request.args.get('url')
        
        if not youtube_url:
            return jsonify({
                'status': False,
                'error': 'Missing URL parameter',
                'message': 'Please provide a YouTube URL'
            }), 400
        
        # Get video info only
        from services.youtube_downloader import YouTubeDownloader
        downloader = YouTubeDownloader()
        
        result = run_async(downloader.get_video_info(youtube_url))
        
        return jsonify({
            'status': True,
            'video_id': downloader.extract_video_id(youtube_url),
            'title': result['title'],
            'duration': result['duration'],
            'thumbnail': result['thumbnail']
        })
        
    except Exception as e:
        logger.error(f"Info API error: {e}")
        return jsonify({
            'status': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500



@api_bp.route('/cache/stats', methods=['GET'])
def get_cache_stats():
    """Get cache statistics"""
    try:
        from database.mongo import get_content_cache_collection
        
        cache_collection = get_content_cache_collection()
        
        # Get cache stats
        total_cached = run_async(cache_collection.count_documents({}))
        video_cached = run_async(cache_collection.count_documents({'file_type': 'video'}))
        audio_cached = run_async(cache_collection.count_documents({'file_type': 'audio'}))
        
        # Get most accessed content
        pipeline = [
            {'$sort': {'access_count': -1}},
            {'$limit': 10},
            {'$project': {
                'title': 1,
                'youtube_id': 1,
                'file_type': 1,
                'access_count': 1,
                'created_at': 1
            }}
        ]
        
        most_accessed = run_async(cache_collection.aggregate(pipeline).to_list(None))
        
        return jsonify({
            'status': True,
            'cache_stats': {
                'total_cached': total_cached,
                'video_cached': video_cached,
                'audio_cached': audio_cached,
                'most_accessed': most_accessed
            }
        })
        
    except Exception as e:
        logger.error(f"Cache stats API error: {e}")
        return jsonify({
            'status': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@api_bp.after_request
def after_request(response):
    """Clean up after request"""
    try:
        # Unregister concurrent user
        session_id = session.get('session_id')
        if session_id:
            run_async(api_service.unregister_concurrent_user(session_id))
    except Exception as e:
        logger.error(f"After request cleanup error: {e}")
    
    return response
