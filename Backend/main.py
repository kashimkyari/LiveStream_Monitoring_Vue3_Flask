#!/usr/bin/env python3
"""
main.py - Flask application entry point with SSL support and Socket.IO integration
"""

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

# Get the socketio instance from utils
from utils.notifications import get_socketio
socketio = get_socketio()

if not socketio:
    logging.error("Socket.IO not properly initialized")
    raise RuntimeError("Socket.IO initialization failed")
else:
    logging.info(f"Socket.IO initialized with async_mode: {socketio.async_mode}")

# Parse ALLOWED_ORIGINS from environment
allowed_origins = os.getenv('ALLOWED_ORIGINS', '*').split(',')
vercel_domain = 'https://live-stream-monitoring-vue3-flask.vercel.app'
logging.info(f"Configured allowed origins: {allowed_origins}")

# === CORS Configuration for Flask ===
CORS(app, 
     origins=allowed_origins,
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# === CORS Configuration for Socket.IO ===
if vercel_domain not in allowed_origins:
    allowed_origins.append(vercel_domain)
logging.info(f"Configured allowed origins: {allowed_origins}")
# This is crucial for Socket.IO connections
if '*' in allowed_origins:
    socketio.cors_allowed_origins = allowed_origins + ['https://live-stream-monitoring-vue3-flask.vercel.app']
    
else:
    socketio.cors_allowed_origins = allowed_origins
    
logging.info(f"Socket.IO CORS configured with: {socketio.cors_allowed_origins}")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    """Handle OPTIONS requests for all routes to support CORS preflight requests"""
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        
        # Set CORS headers
        origin = request.headers.get('Origin')
        
        if origin in allowed_origins or not allowed_origins or '' in allowed_origins or '*' in allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = origin
        
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        
        return response

# In main.py
@app.before_request
def enforce_https():
    if not request.is_secure and os.getenv('ENABLE_SSL') == 'true':
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)

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
        raise FileNotFoundError(f"Missing SSL certs in {cert_dir}")
    
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
        debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'false',
        use_reloader=False,
        ssl_context=ssl_ctx
    )