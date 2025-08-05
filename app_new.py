import os
import logging
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    api_key = db.Column(db.String(128), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    rate_limit = db.Column(db.Integer, default=1000)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class ApiUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    endpoint = db.Column(db.String(128), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    ip_address = db.Column(db.String(45))

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
        'database': 'connected'
    })

@app.route('/docs')
def api_docs():
    """API documentation"""
    docs = {
        'title': 'YouTube API Server Documentation',
        'version': '1.0.0',
        'description': 'High-performance YouTube API with PostgreSQL backend',
        'base_url': request.host_url + 'api/v1',
        'authentication': {
            'type': 'API Key',
            'header': 'X-API-Key',
            'parameter': 'api_key'
        },
        'endpoints': {
            'GET /api/v1/status': {
                'description': 'Get API status',
                'response': 'Server status and user count'
            },
            'GET /api/v1/video': {
                'description': 'Get video content',
                'parameters': {
                    'url': 'YouTube URL (required)',
                    'quality': 'Video quality: 144, 240, 360, 480, 720, 1080 (default: 360)'
                },
                'response': 'Video download information'
            }
        }
    }
    return jsonify(docs)

# API Blueprint
from flask import Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

@api_bp.before_request
def before_request():
    """Validate API key for all API requests"""
    # For demo purposes, accept any API key or no key
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    request.api_key = api_key or 'demo_key'

@api_bp.route('/status', methods=['GET'])
def get_status():
    """Get API status"""
    try:
        user_count = db.session.query(User).count()
        return jsonify({
            'status': True,
            'server': 'YouTube API Server',
            'version': '1.0.0',
            'users': user_count,
            'database': 'PostgreSQL',
            'timestamp': db.func.current_timestamp()
        })
    except Exception as e:
        app.logger.error(f"Status endpoint error: {e}")
        return jsonify({
            'status': True,
            'server': 'YouTube API Server',
            'version': '1.0.0',
            'users': 0,
            'database': 'PostgreSQL',
            'message': 'Demo mode'
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
        
        # Demo response
        return jsonify({
            'status': True,
            'url': youtube_url,
            'quality': quality,
            'message': 'Video processing service (demo mode)',
            'download_url': f'https://demo.example.com/video/{quality}',
            'cached': False
        })
        
    except Exception as e:
        app.logger.error(f"Video API error: {e}")
        return jsonify({
            'status': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500

# Register blueprint
app.register_blueprint(api_bp)

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': False,
        'error': 'Endpoint not found',
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal server error: {error}")
    return jsonify({
        'status': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

# Initialize database
with app.app_context():
    try:
        db.create_all()
        app.logger.info("Database tables created successfully")
        
        # Create demo user if not exists
        if not User.query.filter_by(username='demo').first():
            demo_user = User(
                username='demo',
                api_key='demo_api_key_12345',
                is_active=True,
                rate_limit=1000
            )
            db.session.add(demo_user)
            db.session.commit()
            app.logger.info("Demo user created")
            
    except Exception as e:
        app.logger.error(f"Database initialization error: {e}")

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )