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
from datetime import datetime

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
    cors_allowed_origins=os.getenv('ALLOWED_ORIGINS', 'https://live-stream-monitoring-vue3-flask.vercel.app').split(','),
    path="/ws",
    async_mode='threading',    # Use threading mode for better compatibility
    logger=True,               # Enable Socket.IO logging
    engineio_logger=True       # Enable Engine.IO logging for debugging
)

# Allowed frontends (comma‑separated in .env)
ALLOWED_ORIGINS = os.getenv(
    'ALLOWED_ORIGINS',
    'https://live-stream-monitoring-vue3-flask.vercel.app'
).split(',')

# Add security headers to prevent mixed content issues
def add_security_headers(response):
    """Add security headers to the Flask response"""
    # Add security headers that help prevent various attacks
    response.headers['X-Content-Type-Options'] = "nosniff"
    response.headers['X-Frame-Options'] = "SAMEORIGIN"
    response.headers['X-XSS-Protection'] = "1; mode=block"
    response.headers['Referrer-Policy'] = "strict-origin-when-cross-origin"
    
    # Only add strict HTTPS headers if running in SSL mode
    if os.getenv('ENABLE_SSL', 'false').lower() == 'true':
        response.headers['Strict-Transport-Security'] = "max-age=31536000; includeSubDomains"
        response.headers['Content-Security-Policy'] = "upgrade-insecure-requests; default-src 'self' https:; script-src 'self' https:; img-src 'self' https: data:; style-src 'self' https: 'unsafe-inline'; font-src 'self' https:; connect-src 'self' https: wss:;"
    
    return response

app.after_request(add_security_headers)

# === Dynamic CORS Handler ===
@app.after_request
def apply_cors(response):
    origin = request.headers.get('Origin')
    
    # Check if origin is in allowed origins
    if origin and origin in ALLOWED_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
    elif origin:
        # For development, you might want to allow any origin
        # but in production, consider being more restrictive
        if app.debug:
            response.headers['Access-Control-Allow-Origin'] = origin
        else:
            # Default to the first allowed origin
            response.headers['Access-Control-Allow-Origin'] = ALLOWED_ORIGINS[0]
    else:
        # If no origin header, use the first allowed origin
        response.headers['Access-Control-Allow-Origin'] = ALLOWED_ORIGINS[0]
    
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
    # Get the protocol based on SSL configuration
    protocol = "https" if os.getenv('ENABLE_SSL', 'false').lower() == 'true' else "http"
    host = request.headers.get('Host', 'localhost:5000')
    
    # Construct a proper URL with protocol
    socket_url = f"{protocol}://{host}"
    
    return jsonify({
        'socket_url': socket_url,
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
    from utils.notifications import emit_notification
    start_notification_monitor()
    start_detection_cleanup_thread()
    
    # Create a notification data structure
    notification_data = {
        'type': 'system',
        'message': 'Server started successfully',
        'level': 'info',
        'timestamp': datetime.now().isoformat()
    }
    
    emit_notification(notification_data)

    logging.info("Background services started")
except Exception as e:
    logging.error("Background services failed: %s", e)

if __name__ == "__main__":
    # Get environment variables with sensible defaults
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    # Configure SSL based on environment variable
    if os.getenv('ENABLE_SSL', 'false').lower() == 'true':
        # Get certificate directory with home directory expansion
        cert_dir = os.path.expanduser(os.getenv('CERT_DIR', '~/certs'))
        
        # Define paths to certificate files
        ssl_cert = os.path.join(cert_dir, 'fullchain.pem')
        ssl_key = os.path.join(cert_dir, 'privkey.pem')
        
        # Check if certificates exist
        if not os.path.exists(cert_dir):
            logging.error(f"Certificate directory does not exist: {cert_dir}")
            logging.error("Creating directory and generating self-signed certificates...")
            
            try:
                # Create directory
                os.makedirs(cert_dir, exist_ok=True)
                
                # Generate self-signed certificates using OpenSSL
                import subprocess
                
                # Change to certificate directory
                os.chdir(cert_dir)
                
                # Generate certificate
                subprocess.run([
                    'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
                    '-keyout', 'privkey.pem', '-out', 'fullchain.pem',
                    '-days', '365', '-nodes', '-subj',
                    '/CN=localhost'
                ], check=True)
                
                logging.info(f"Self-signed certificates generated in {cert_dir}")
                
                # Now set SSL context with the newly generated certificates
                ssl_ctx = (ssl_cert, ssl_key)
            except Exception as e:
                logging.error(f"Failed to generate self-signed certificates: {str(e)}")
                logging.warning("Falling back to HTTP mode")
                ssl_ctx = None
        elif not (os.path.exists(ssl_cert) and os.path.exists(ssl_key)):
            logging.error(f"Missing SSL certificates in {cert_dir}")
            logging.error(f"Looking for: {ssl_cert} and {ssl_key}")
            logging.warning("Falling back to HTTP mode")
            ssl_ctx = None
        else:
            # Certificates exist, use them
            ssl_ctx = (ssl_cert, ssl_key)
            logging.info(f"Using SSL certificates: {ssl_cert} and {ssl_key}")
    else:
        # SSL not enabled
        ssl_ctx = None
        logging.info("Running without SSL (HTTP mode)")
    
    # Log startup information
    ssl_status = "HTTPS" if ssl_ctx else "HTTP"
    logging.info(f"Starting server in {ssl_status} mode on {host}:{port} (Debug: {debug})")
    
    # Use socketio.run instead of app.run for Socket.IO support
    try:
        socketio.run(
            app, 
            host=host, 
            port=port, 
            debug=debug,
            ssl_context=ssl_ctx,
            # For compatibility with Flask-SocketIO
            use_reloader=debug,
            # Allow unsafe werkzeug in development mode
            allow_unsafe_werkzeug=debug
        )
    except Exception as e:
        logging.error(f"Failed to start server: {str(e)}")
        
        # Provide helpful error message for common SSL issues
        if ssl_ctx and "SSL" in str(e):
            logging.error("SSL configuration error. Check your certificates or try running without SSL.")
            logging.error("To disable SSL, set ENABLE_SSL=false in your .env file.")