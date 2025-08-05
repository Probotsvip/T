from flask import Blueprint, request, Response, session, jsonify
import asyncio
import uuid
from services.api_service import api_service
from services.telegram_cache import TelegramCache

# Initialize the full Telegram cache system
telegram_cache = TelegramCache()
from utils.logging import LOGGER

logger = LOGGER(__name__)

streaming_bp = Blueprint('streaming', __name__, url_prefix='/stream')

def run_async(coro):
    """Helper to run async functions in Flask routes"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@streaming_bp.before_request
def before_streaming_request():
    """Validate API key for streaming requests"""
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    
    if not api_key:
        return jsonify({
            'status': False,
            'error': 'API key required for streaming'
        }), 401
    
    # Validate API key
    key_data = run_async(api_service.validate_api_key(api_key))
    
    if not key_data:
        return jsonify({
            'status': False,
            'error': 'Invalid API key'
        }), 401
    
    if 'error' in key_data:
        return jsonify({
            'status': False,
            'error': key_data['error']
        }), 429
    
    request.api_key = api_key
    request.key_data = key_data

@streaming_bp.route('/video/<video_id>')
def stream_video(video_id):
    """Stream video content directly from Telegram cache"""
    try:
        quality = request.args.get('quality', '360')
        
        # Check cache
        cached_content = run_async(telegram_cache.check_cache(video_id, 'video', quality))
        
        if not cached_content:
            return jsonify({
                'status': False,
                'error': 'Content not found in cache',
                'message': 'Please request the content first via /api/v1/video endpoint'
            }), 404
        
        # Get streaming URL from Telegram
        stream_url = run_async(telegram_cache.get_file_stream_url(cached_content['telegram_file_id']))
        
        if not stream_url:
            return jsonify({
                'status': False,
                'error': 'Streaming URL not available'
            }), 500
        
        # Register streaming session
        session_id = session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
        
        run_async(api_service.register_concurrent_user(session_id, request.api_key, 'stream_video'))
        
        # Stream the content
        def generate():
            try:
                import httpx
                with httpx.stream('GET', stream_url) as response:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        yield chunk
            except Exception as e:
                logger.error(f"Streaming error: {e}")
        
        return Response(
            generate(),
            mimetype='video/mp4',
            headers={
                'Content-Disposition': f'inline; filename="{cached_content["title"]}.mp4"',
                'Accept-Ranges': 'bytes',
                'Cache-Control': 'public, max-age=3600'
            }
        )
        
    except Exception as e:
        logger.error(f"Video streaming error: {e}")
        return jsonify({
            'status': False,
            'error': 'Streaming failed',
            'message': str(e)
        }), 500

@streaming_bp.route('/audio/<video_id>')
def stream_audio(video_id):
    """Stream audio content directly from Telegram cache"""
    try:
        # Check cache
        cached_content = run_async(telegram_cache.check_cache(video_id, 'audio'))
        
        if not cached_content:
            return jsonify({
                'status': False,
                'error': 'Content not found in cache',
                'message': 'Please request the content first via /api/v1/audio endpoint'
            }), 404
        
        # Get streaming URL from Telegram
        stream_url = run_async(telegram_cache.get_file_stream_url(cached_content['telegram_file_id']))
        
        if not stream_url:
            return jsonify({
                'status': False,
                'error': 'Streaming URL not available'
            }), 500
        
        # Register streaming session
        session_id = session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
        
        run_async(api_service.register_concurrent_user(session_id, request.api_key, 'stream_audio'))
        
        # Stream the content
        def generate():
            try:
                import httpx
                with httpx.stream('GET', stream_url) as response:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        yield chunk
            except Exception as e:
                logger.error(f"Streaming error: {e}")
        
        return Response(
            generate(),
            mimetype='audio/mpeg',
            headers={
                'Content-Disposition': f'inline; filename="{cached_content["title"]}.mp3"',
                'Accept-Ranges': 'bytes',
                'Cache-Control': 'public, max-age=3600'
            }
        )
        
    except Exception as e:
        logger.error(f"Audio streaming error: {e}")
        return jsonify({
            'status': False,
            'error': 'Streaming failed',
            'message': str(e)
        }), 500

@streaming_bp.route('/direct')
def direct_stream():
    """Direct streaming from external URL (fallback)"""
    try:
        url = request.args.get('url')
        content_type = request.args.get('type', 'video')
        
        if not url:
            return jsonify({
                'status': False,
                'error': 'URL parameter required'
            }), 400
        
        # Register streaming session
        session_id = session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
        
        run_async(api_service.register_concurrent_user(session_id, request.api_key, 'direct_stream'))
        
        # Stream from external URL
        def generate():
            try:
                import httpx
                with httpx.stream('GET', url, timeout=300.0) as response:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        yield chunk
            except Exception as e:
                logger.error(f"Direct streaming error: {e}")
        
        mimetype = 'audio/mpeg' if content_type == 'audio' else 'video/mp4'
        extension = 'mp3' if content_type == 'audio' else 'mp4'
        
        return Response(
            generate(),
            mimetype=mimetype,
            headers={
                'Content-Disposition': f'inline; filename="stream.{extension}"',
                'Accept-Ranges': 'bytes',
                'Cache-Control': 'no-cache'
            }
        )
        
    except Exception as e:
        logger.error(f"Direct streaming error: {e}")
        return jsonify({
            'status': False,
            'error': 'Direct streaming failed',
            'message': str(e)
        }), 500

@streaming_bp.after_request 
def after_streaming_request(response):
    """Clean up after streaming request"""
    try:
        session_id = session.get('session_id')
        if session_id:
            run_async(api_service.unregister_concurrent_user(session_id))
    except Exception as e:
        logger.error(f"Streaming cleanup error: {e}")
    
    return response
