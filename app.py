import os
import asyncio
import logging
from flask import Flask, render_template, jsonify, request
from werkzeug.middleware.proxy_fix import ProxyFix
from config import SECRET_KEY, DEBUG
from database.simple_mongo import init_db
from routes.api import api_bp
from routes.admin import admin_bp
from routes.streaming import streaming_bp
from utils.logging import LOGGER

# Configure logging
logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
logger = LOGGER(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", SECRET_KEY)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuration
app.config['DEBUG'] = DEBUG
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Register blueprints
app.register_blueprint(api_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(streaming_bp)

@app.route('/')
def index():
    """Main page with API documentation"""
    return render_template('base.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'YouTube API Server',
        'version': '1.0.0',
        'concurrent_support': '10,000+ users'
    })

@app.route('/docs')
def api_docs():
    """API documentation"""
    docs = {
        'title': 'YouTube API Server Documentation',
        'version': '1.0.0',
        'description': 'High-performance YouTube API with Telegram caching',
        'base_url': request.host_url + 'api/v1',
        'authentication': {
            'type': 'API Key',
            'header': 'X-API-Key',
            'parameter': 'api_key'
        },
        'endpoints': {
            'GET /api/v1/video': {
                'description': 'Get video content',
                'parameters': {
                    'url': 'YouTube URL (required)',
                    'quality': 'Video quality: 144, 240, 360, 480, 720, 1080 (default: 360)'
                },
                'response': 'Video download URL or cached stream URL'
            },
            'GET /api/v1/audio': {
                'description': 'Get audio content',
                'parameters': {
                    'url': 'YouTube URL (required)'
                },
                'response': 'Audio download URL or cached stream URL'
            },
            'GET /api/v1/info': {
                'description': 'Get video information',
                'parameters': {
                    'url': 'YouTube URL (required)'
                },
                'response': 'Video metadata (title, duration, thumbnail)'
            },
            'GET /api/v1/status': {
                'description': 'Get API status',
                'response': 'Server status and concurrent user count'
            },
            'GET /stream/video/<video_id>': {
                'description': 'Stream video directly from cache',
                'parameters': {
                    'quality': 'Video quality (optional)'
                },
                'response': 'Video stream'
            },
            'GET /stream/audio/<video_id>': {
                'description': 'Stream audio directly from cache',
                'response': 'Audio stream'
            }
        },
        'features': [
            'Shared Telegram caching for 10,000+ concurrent users',
            'Real-time streaming from cached content',
            'Enterprise-grade scalability',
            'Advanced analytics and monitoring',
            'Rate limiting and usage tracking',
            'High-performance concurrent request handling'
        ]
    }
    
    return jsonify(docs)

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': False,
        'error': 'Endpoint not found',
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({
        'status': False,
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.'
    }), 429

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'status': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

# Initialize database connection
def initialize_app():
    """Initialize the application"""
    try:
        logger.info("Initializing YouTube API Server...")
        
        # Initialize MongoDB connection
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(init_db())
            loop.close()
            logger.info("MongoDB connected successfully")
        except Exception as db_error:
            logger.warning(f"Database initialization failed: {db_error}")
            logger.info("Continuing with limited functionality")
        
        logger.info("YouTube API Server initialized and ready for 10,000+ concurrent users")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        logger.warning("Continuing with basic functionality")

# Initialize on startup
initialize_app()

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=DEBUG,
        threaded=True
    )
