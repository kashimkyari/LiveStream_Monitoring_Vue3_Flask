#!/usr/bin/env python3
"""
main.py - Flask application entry point
"""
import gevent.monkey
gevent.monkey.patch_all()

import logging
import os
import time
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

from config import create_app
from utils.notifications import init_socketio
from extensions import db
from models import User

# Initialize Flask app
app = create_app()

# Initialize SocketIO
socketio = init_socketio(app)

# Parse allowed origins from environment
allowed_origins = os.getenv('ALLOWED_ORIGINS', 'https://monitor.jetcamstudio.com,http://localhost:8080').split(',')

# Log CORS configuration
app.config['CORS_ALLOWED_ORIGINS'] = allowed_origins
logging.info("Configured for CORS with credentials support and HTTPS compatibility")
logging.info(f"Configured allowed origins: {allowed_origins}")

# === CORS Configuration for Flask ===
CORS(app,
     origins=allowed_origins,
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Cache-Control"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     expose_headers=["Content-Length", "X-JSON"],
     max_age=600)

# Register a before_request handler for CORS
@app.before_request
def handle_preflight():
    """Special handling for CORS preflight requests"""
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        origin = request.headers.get('Origin', '*')
        
        if origin in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin, Cache-Control'
            response.headers['Access-Control-Max-Age'] = '600'
        return response

# Add after_request handler to set CORS headers for all responses
@app.after_request
def add_cors_headers(response):
    """Add CORS headers to all responses"""
    origin = request.headers.get('Origin')
    if origin and origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin, Cache-Control'
    return response

# Add CORS test endpoint for debugging
@app.route('/cors-test', methods=['GET', 'OPTIONS'])
def cors_test():
    """Test endpoint for CORS configuration"""
    if request.method == 'OPTIONS':
        return app.make_default_options_response()
    
    return jsonify({
        "message": "CORS test successful",
        "your_origin": request.headers.get('Origin', 'No origin header'),
        "request_protocol": request.headers.get('X-Forwarded-Proto', 'https'),
        "request_headers": dict(request.headers),
        "cors_enabled": True,
        "cors_mode": "HTTPS with credentials enabled",
        "credentials_supported": True
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

# === Background Services ===
with app.app_context():
    try:
        from utils.notifications import emit_notification
        from monitoring import start_notification_monitor
        
        time.sleep(1)
        start_notification_monitor()
        emit_notification({'system': 'Server started successfully', 'event_type': 'server_start'})
        logging.info("Background services initialized")
    
    except Exception as e:
        logging.error(f"Background services error: {str(e)}")

# === Health Check Endpoint ===
@app.route('/check-health', methods=['GET'])
def health_check():
    """Health check endpoint for load balancers and monitoring"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "version": os.getenv('APP_VERSION', '1.0.0')
    })

# === SSL Configuration Helper ===
def configure_ssl_context():
    """Configure SSL context for the Flask application"""
    ssl_context = None
    enable_ssl = os.getenv('ENABLE_SSL', 'true').lower() == 'true'
    
    if enable_ssl:
        cert_dir = os.getenv('CERT_DIR', '/home/ec2-user/LiveStream_Monitoring_Vue3_Flask/backend')
        certfile = os.getenv('SSL_CERT_PATH', os.path.join(cert_dir, 'fullchain.pem'))
        keyfile = os.getenv('SSL_KEY_PATH', os.path.join(cert_dir, 'privkey.pem'))
        
        if os.path.exists(certfile) and os.path.exists(keyfile):
            ssl_context = (certfile, keyfile)
            logging.info(f"SSL Enabled with cert: {certfile} and key: {keyfile}")
        else:
            logging.error(f"SSL certificate files not found at {certfile} and {keyfile}")
            raise FileNotFoundError("SSL certificate files not found")
            
    return ssl_context

# === Main Execution ===
if __name__ == "__main__":
    ssl_context = configure_ssl_context()
    server_mode = "HTTPS" if ssl_context else "HTTP"
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    logging.info(f"Starting server in {server_mode} mode with debug={'enabled' if debug_mode else 'disabled'}")
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=debug_mode,
        use_reloader=debug_mode,
        allow_unsafe_werkzeug=True,  # Required for gevent with Werkzeug >= 2.0
        engineio_options={
            'async_mode': 'gevent',
            'cors_allowed_origins': allowed_origins
        }
    )