#!/usr/bin/env python3
"""
main.py - Flask application entry point with SSL support, robust CORS, and Socket.IO integration.
"""

import logging
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
import secrets
import string

# Import the updated create_app function that returns both app and socketio
from config import create_app
from extensions import db
from models import User, Stream
from routes import *
from cleanup import start_chat_cleanup_thread, start_detection_cleanup_thread
from monitoring import start_notification_monitor
from flask_socketio import SocketIO, emit


load_dotenv()

# Create the Flask app and initialize Socket.IO with threading mode
app, socketio = create_app()

# Configure Socket.IO with better compatibility settings
socketio.init_app(
    app, 
    cors_allowed_origins="*",  # Allow all origins for WebSocket
    path="/ws",
    async_mode='threading',    # Use threading mode for better compatibility
    logger=True,               # Enable Socket.IO logging
    engineio_logger=True       # Enable Engine.IO logging for debugging
)

# Allowed frontends (comma‑separated in .env)
ALLOWED_ORIGINS = os.getenv(
    'ALLOWED_ORIGINS',
    'https://live-stream-monitoring-vue3-flask.vercel.app,http://localhost:8080,102.90.45.224,http://127.0.0.1:5173'
).split(',')

# === Dynamic CORS Handler ===
@app.after_request
def apply_cors(response):
    # Allow requests from all origins
    response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*') 
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-Requested-With'
    return response

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler('app.log'), logging.StreamHandler()]
)

@app.route('/socket-info')
def socket_info():
    """Return Socket.IO connection information for clients"""
    return jsonify({
        'socket_url': request.host_url.rstrip('/'),
        'path': '/ws',
        'namespaces': {
            'notifications': '/notifications'
        }
    })


# Socket.IO error handler
@socketio.on_error_default
def default_error_handler(e):
    logging.error(f"Socket.IO error: {str(e)}")

# Socket.IO WebSocket specific error handler
@socketio.on_error('/ws')
def ws_error_handler(e):
    logging.error(f"WebSocket error: {str(e)}")

with app.app_context():
    try:
        # Create tables in the correct order
        # First, we'll create the base tables
        db.create_all()
        logging.info("Database tables initialized")
        
        # Check if admin user exists, create if not
        admin_exists = User.query.filter_by(role='admin').first()
        if not admin_exists:
            # Get required admin credentials from environment variables
            admin_username = os.getenv('DEFAULT_ADMIN_USERNAME')
            admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD')
            admin_email = os.getenv('DEFAULT_ADMIN_EMAIL')
            
            # Verify all required environment variables are set
            if not all([admin_username, admin_password, admin_email]):
                # Generate a secure random password if not provided
                if not admin_password:
                    chars = string.ascii_letters + string.digits + string.punctuation
                    admin_password = ''.join(secrets.choice(chars) for _ in range(16))
                    logging.warning(f"Admin password not found in environment. Generated secure password: {admin_password}")
                    logging.warning("IMPORTANT: Please save this password and set it in your environment variables!")
                else:
                    logging.error("Missing required admin credentials in environment variables")
                    logging.error("Please set DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD, and DEFAULT_ADMIN_EMAIL")
            
            # Create admin user with proper password hashing
            admin_user = User(
                username=admin_username or "admin",  # Fallback only for username
                password=generate_password_hash(admin_password),  # Hash the password
                role='admin',
                email=admin_email or "admin@example.com",  # Fallback only for email
                receive_updates=True
            )
            db.session.add(admin_user)
            db.session.commit()
            logging.info("Default admin user created")
        else:
            logging.info("Admin user already exists")
                
    except Exception as e:
        logging.error("DB init failed: %s", e)
        raise

try:
    # Import socket_events here (after socketio init) to register the events
    from socket_events import register_socket_events
    register_socket_events(socketio)
    
    start_notification_monitor()
    start_detection_cleanup_thread()
    logging.info("Background services started")
except Exception as e:
    logging.error("Background services failed: %s", e)

if __name__ == "__main__":
    debug = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    if os.getenv('ENABLE_SSL', 'false').lower() == 'true':
        cert_dir = os.path.expanduser(os.getenv('CERT_DIR', '~/certs'))
        ssl_cert = os.path.join(cert_dir, 'fullchain.pem')
        ssl_key = os.path.join(cert_dir, 'privkey.pem')
        if not (os.path.exists(ssl_cert) and os.path.exists(ssl_key)):
            logging.error("Missing SSL certs in %s", cert_dir)
            raise FileNotFoundError("Certs missing")
        ssl_ctx = (ssl_cert, ssl_key)
    else:
        ssl_ctx = None
        logging.info("Running without SSL")
    
    # Use socketio.run instead of app.run for Socket.IO support
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=5000, 
        debug=debug,
        ssl_context=ssl_ctx,
        # For compatibility with Flask-SocketIO
        use_reloader=debug,
        # Allow unsafe werkzeug in development mode
        allow_unsafe_werkzeug=debug
    )