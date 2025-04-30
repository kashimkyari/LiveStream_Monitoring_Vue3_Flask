#!/usr/bin/env python3
"""
main.py - Flask application entry point with Socket.IO integration
"""
# Import gevent and apply monkey patching at the very top
from gevent import monkey
monkey.patch_all()

import logging
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash
import secrets
import string
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

load_dotenv()

# Import after monkey patching but before app creation
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
    # Explicitly set async_mode to 'gevent' for consistency
    socketio.async_mode = 'gevent'
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

# Add CORS test endpoint for debugging
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

# === Import and register socket events BEFORE background services ===
from socket_events import register_socket_events
register_socket_events(socketio)

# === Background Services ===
with app.app_context():
    try:
        from utils.notifications import emit_notification
        from messaging import register_messaging_events
        from monitoring import start_notification_monitor
        
        # Register messaging events
        register_messaging_events()
        
        # Start background services
        start_notification_monitor()
        
        # Notify of server start
        emit_notification({'system': 'Server started successfully', 'event_type': 'server_start'})
        logging.info("Background services initialized")
    
    except Exception as e:
        logging.error(f"Background services error: {str(e)}")

# === Main Execution ===
if __name__ == "__main__":
    # Run with socketio for development using Gevent
    socketio.run(
        app,
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true',
        use_reloader=False
    )