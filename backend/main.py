#!/usr/bin/env python3
"""
main.py - Flask application entry point with SSL support and Socket.IO integration
"""
from gevent import monkey
monkey.patch_all()
import logging
import os
import ssl
from dotenv import load_dotenv
from flask import Flask, request, jsonify, redirect
from werkzeug.security import generate_password_hash
import secrets
import string
from flask_cors import CORS

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import after Flask app creation
from config import create_app
from extensions import db
from models import User

# Initialize Flask app
app = create_app()

# Parse ALLOWED_ORIGINS from environment
allowed_origins = os.getenv('ALLOWED_ORIGINS', 'https://live-stream-monitoring-vue3-flask.vercel.app,http://localhost:8080,https://jetcamstudios-git-main-kashimkyaris-projects.vercel.app,https://jetcamstudios-kashimkyaris-projects.vercel.app').split(',')
vercel_domain = 'https://live-stream-monitoring-vue3-flask.vercel.app'

# Add the production domain if not already in the list
if vercel_domain not in allowed_origins and vercel_domain.strip():
    allowed_origins.append(vercel_domain)

# Store allowed origins in app config for consistent access across blueprints
app.config['CORS_ALLOWED_ORIGINS'] = allowed_origins

# Log configured allowed origins
logging.info(f"Configured allowed origins: {allowed_origins}")

# === CORS Configuration for Flask ===
# Use a wider set of allowed headers
CORS(app, 
     origins=allowed_origins,
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Cache-Control"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     expose_headers=["Content-Length", "X-JSON"],
     max_age=600)  # 10 minutes cache for preflight requests

# Get the socketio instance from utils
from utils.notifications import get_socketio
socketio = get_socketio()

if not socketio:
    logging.error("Socket.IO not properly initialized")
    raise RuntimeError("Socket.IO initialization failed")
else:
    logging.info(f"Socket.IO initialized with async_mode: {socketio.async_mode}")

# === CORS Configuration for Socket.IO ===
if '*' in allowed_origins:
    socketio.cors_allowed_origins = "*"  # Accept all origins
else:
    socketio.cors_allowed_origins = allowed_origins

# Register a before_request handler for CORS
@app.before_request
def handle_preflight():
    """Special handling for CORS preflight requests"""
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        
        # Get origin from the request headers
        origin = request.headers.get('Origin')
        
        # Check if the origin is allowed
        if origin in allowed_origins or '*' in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
        else:
            # Default to the first allowed origin if specific ones are configured
            response.headers['Access-Control-Allow-Origin'] = allowed_origins[0] if allowed_origins and allowed_origins[0] != '*' else '*'
        
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin, Cache-Control'
        response.headers['Access-Control-Max-Age'] = '600'  # Cache preflight response for 10 minutes
        
        return response

# In main.py
@app.before_request
def enforce_https():
    if not request.is_secure and os.getenv('ENABLE_SSL') == 'true':
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)

# === Enhanced CORS Configuration ===

# 1. Extract CORS configuration to a separate function for cleaner organization
def configure_cors(app, allowed_origins):
    """Configure CORS for both Flask and Socket.IO"""
    logging.info(f"Configuring CORS with allowed origins: {allowed_origins}")
    
    # Configure Flask-CORS
    CORS(app, 
         origins=allowed_origins,
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization", "X-Requested-With", 
                       "Accept", "Origin", "Cache-Control"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         expose_headers=["Content-Length", "X-JSON"],
         max_age=600)  # 10 minutes cache for preflight requests
    
    # Configure Socket.IO CORS
    socketio = get_socketio()
    if '*' in allowed_origins:
        socketio.cors_allowed_origins = "*"
    else:
        socketio.cors_allowed_origins = allowed_origins
    
    # Add CORS debugging middleware
    @app.before_request
    def log_cors_requests():
        """Log CORS-related requests for debugging"""
        # Only log if debug mode is enabled
        if app.debug and (request.method == 'OPTIONS' or 
                         'Origin' in request.headers):
            origin = request.headers.get('Origin', 'No origin')
            logging.info(f"CORS Request - Method: {request.method}, "
                         f"Path: {request.path}, Origin: {origin}")
    
    # Enhanced preflight handler
    @app.before_request
    def handle_preflight():
        """Special handling for CORS preflight requests"""
        if request.method == 'OPTIONS':
            response = app.make_default_options_response()
            
            # Get origin from the request headers
            origin = request.headers.get('Origin')
            
            # Check if the origin is allowed
            if origin in allowed_origins or '*' in allowed_origins:
                response.headers['Access-Control-Allow-Origin'] = origin
            elif allowed_origins and allowed_origins[0] != '*':
                # Default to the first allowed origin if specific ones are configured
                response.headers['Access-Control-Allow-Origin'] = allowed_origins[0]
            else:
                response.headers['Access-Control-Allow-Origin'] = '*'
            
            # Set other CORS headers
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin, Cache-Control'
            response.headers['Access-Control-Max-Age'] = '600'
            
            if app.debug:
                logging.info(f"Responding to OPTIONS with ACAO: {response.headers['Access-Control-Allow-Origin']}")
            
            return response

    # Add after_request handler for consistent CORS headers on all responses
    @app.after_request
    def add_cors_headers(response):
        """Add CORS headers to all responses"""
        # Skip if this is an OPTIONS request (already handled)
        if request.method != 'OPTIONS':
            origin = request.headers.get('Origin')
            
            # Set CORS headers based on origin
            if origin in allowed_origins or '*' in allowed_origins:
                response.headers['Access-Control-Allow-Origin'] = origin
            elif allowed_origins and allowed_origins[0] != '*':
                response.headers['Access-Control-Allow-Origin'] = allowed_origins[0]
            else:
                response.headers['Access-Control-Allow-Origin'] = '*'
                
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            
        return response
    
    # Add enhanced CORS test endpoint
    @app.route('/cors-test', methods=['GET', 'OPTIONS'])
    def cors_test():
        """Test endpoint for CORS configuration"""
        if request.method == 'OPTIONS':
            # Let the before_request handler handle this
            return app.make_default_options_response()
        
        return jsonify({
            "message": "CORS test successful",
            "your_origin": request.headers.get('Origin', 'No origin header'),
            "allowed_origins": allowed_origins,
            "request_headers": dict(request.headers),
            "cors_enabled": True
        })

    return app

# 2. Function to normalize origins for consistent comparison
def normalize_origins(origins_list):
    """Normalize origins to ensure consistent format"""
    normalized = []
    for origin in origins_list:
        origin = origin.strip()
        if origin and origin != '*':
            # Remove trailing slashes
            if origin.endswith('/'):
                origin = origin[:-1]
            # Include both http and https versions if not already specified
            if origin.startswith('http://') and f"https://{origin[7:]}" not in origins_list:
                normalized.append(origin)
                normalized.append(f"https://{origin[7:]}")
            elif origin.startswith('https://') and f"http://{origin[8:]}" not in origins_list:
                normalized.append(origin)
                normalized.append(f"http://{origin[8:]}")
            else:
                normalized.append(origin)
        elif origin == '*':
            normalized.append(origin)
    
    return normalized

# 3. Main code to configure CORS (to be used in main.py)
def setup_cors_for_app(app):
    """Set up CORS for the application"""
    # Parse ALLOWED_ORIGINS from environment
    allowed_origins = os.getenv('ALLOWED_ORIGINS', '*').split(',')
    
    # Add production domains if not in list
    vercel_domains = [
        'https://live-stream-monitoring-vue3-flask.vercel.app',
        'http://live-stream-monitoring-vue3-flask.vercel.app'
    ]
    
    for domain in vercel_domains:
        if domain not in allowed_origins and domain.strip():
            allowed_origins.append(domain)
    
    # Add localhost for development if not in list
    local_domains = ['http://localhost:8080', 'http://localhost:3000']
    for domain in local_domains:
        if domain not in allowed_origins and domain.strip():
            allowed_origins.append(domain)
    
    # Normalize origins for consistent matching
    allowed_origins = normalize_origins(allowed_origins)
    
    # Store allowed origins in app config
    app.config['CORS_ALLOWED_ORIGINS'] = allowed_origins
    
    # Configure CORS
    return configure_cors(app, allowed_origins)

# === Database Initialization ===
with app.app_context():
    try:
        db.create_all()
        logging.info("Database tables initialized")
        
        # === Admin User Creation ===
        admin_exists = User.query.filter_by(role='admin').first()
        if not admin_exists:
            admin_username = os.getenv('DEFAULT_ADMIN_USERNAME')
            admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD')
            admin_email = os.getenv('DEFAULT_ADMIN_EMAIL')

            if not all([admin_username, admin_password, admin_email]):
                if not admin_password:
                    chars = string.ascii_letters + string.digits + string.punctuation
                    admin_password = ''.join(secrets.choice(chars) for _ in range(16))
                    logging.warning(f"Admin password not found. Generated: {admin_password}")
                    logging.warning("SAVE THIS PASSWORD AND SET ENV VARIABLES!")
                else:
                    logging.error("Missing admin credentials in environment variables")

            admin_user = User(
                username=admin_username or "admin",
                password=generate_password_hash(admin_password),
                role='admin',
                email=admin_email or "admin@example.com",
                receive_updates=True
            )
            db.session.add(admin_user)
            db.session.commit()
            logging.info("Default admin user created")
        else:
            logging.info("Admin user already exists")
                
    except Exception as e:
        logging.error(f"DB init failed: {str(e)}")
        raise

# === Background Services ===
with app.app_context():
    try:
        from socket_events import register_socket_events
        from utils.notifications import emit_notification
        from monitoring import start_notification_monitor
        
        # Register socket events
        register_socket_events(socketio)
        
        # Start background services
        start_notification_monitor()
        
        # Notify of server start
        emit_notification({'system': 'Server started successfully', 'event_type': 'server_start'})
        logging.info("Background services initialized")
    
    except Exception as e:
        logging.error(f"Background services error: {str(e)}")

# === SSL Context Creation ===
def create_ssl_context():
    cert_dir = os.path.expanduser(os.getenv('CERT_DIR', './'))
    ssl_cert = os.path.join(cert_dir, 'fullchain.pem')
    ssl_key = os.path.join(cert_dir, 'privkey.pem')
    
    if not all([os.path.exists(ssl_cert), os.path.exists(ssl_key)]):
        logging.warning(f"SSL certificates not found in {cert_dir}, running without SSL")
        return None
    
    context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(ssl_cert, ssl_key)
    return context

# === Main Execution ===
if __name__ == "__main__":
    ssl_ctx = create_ssl_context() if os.getenv('ENABLE_SSL', 'true').lower() == 'true' else None
    
    # Run with socketio
    socketio.run(
        app,
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true',
        use_reloader=False,
        ssl_context=ssl_ctx
    )