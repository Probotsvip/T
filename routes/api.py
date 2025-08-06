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
    """Validate API key and check daily rate limits for all API requests"""
    if request.endpoint and 'api.' in request.endpoint and request.endpoint != 'api.get_status':
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return jsonify({
                'status': False,
                'error': 'API key required',
                'message': 'Please provide API key in X-API-Key header or api_key parameter'
            }), 401
        
        # Check daily rate limit with automatic midnight reset
        from services.rate_limiter import rate_limiter
        
        try:
            rate_check = rate_limiter.check_and_update_daily_limit(api_key)
            
            if not rate_check['allowed']:
                return jsonify({
                    'status': False,
                    'error': rate_check.get('error', 'Rate limit exceeded'),
                    'daily_requests': rate_check['daily_requests'],
                    'daily_limit': rate_check['daily_limit'],
                    'remaining': rate_check['remaining'],
                    'reset_at': rate_check['reset_at'],
                    'message': f'Daily limit of {rate_check["daily_limit"]} requests exceeded. Resets at midnight (12:00 AM).'
                }), 429
                
            # Store rate limit info in request context
            request.api_key = api_key
            request.rate_info = rate_check
            
            logger.info(f"API Request: {api_key[:10]}... | {rate_check['daily_requests']}/{rate_check['daily_limit']} | {rate_check['remaining']} remaining")
            
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            return jsonify({
                'status': False,
                'error': 'Rate limiting service error',
                'message': 'Please try again later'
            }), 500
        
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
    """Get API status and rate limit info"""
    try:
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        response_data = {
            'status': True,
            'server': 'YouTube API Server',
            'version': '1.0.0',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Add rate limit info if API key provided
        if api_key:
            from services.rate_limiter import rate_limiter
            try:
                stats = rate_limiter.get_api_key_stats(api_key)
                if stats:
                    response_data.update({
                        'api_key_name': stats['key_name'],
                        'daily_requests': stats['daily_requests'],
                        'daily_limit': stats['daily_limit'],
                        'remaining_requests': stats['remaining'],
                        'total_usage': stats['total_usage'],
                        'is_active': stats['is_active'],
                        'daily_reset_at': stats['reset_at'].isoformat() if hasattr(stats['reset_at'], 'isoformat') else str(stats['reset_at'])
                    })
            except Exception as e:
                logger.error(f"Error getting rate limit stats: {e}")
        
        try:
            concurrent_users = run_async(api_service.get_concurrent_user_count())
            response_data['concurrent_users'] = concurrent_users
        except Exception:
            response_data['concurrent_users'] = 0
            
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        return jsonify({
            'status': True,
            'server': 'YouTube API Server',
            'version': '1.0.0',
            'concurrent_users': 1,
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
        # Demo mode cache stats (MongoDB connection required for real stats)
        return jsonify({
            'status': True,
            'cache_stats': {
                'total_cached': 0,
                'video_cached': 0, 
                'audio_cached': 0,
                'most_accessed': [],
                'note': 'Cache statistics will be available when MongoDB is connected'
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
