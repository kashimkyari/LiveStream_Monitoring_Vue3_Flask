#!/usr/bin/env python3
"""
main.py - Flask application entry point
"""
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

# Parse allowed origins from environment but allow all with specific reflection
allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://live-stream-monitoring-vue3-flask.vercel.app,http://localhost:8080,http://jetcamstudios-git-main-kashimkyaris-projects.vercel.app,http://jetcamstudios-kashimkyaris-projects.vercel.app').split(',')

# For debugging - store allowed origins, though we'll reflect any origin back
app.config['CORS_ALLOWED_ORIGINS'] = allowed_origins

# Log CORS configuration
logging.info("Configured for CORS with credentials support and HTTP compatibility")
logging.info(f"Configured default allowed origins (for reference): {allowed_origins}")

# === CORS Configuration for Flask ===
# Custom CORS setup to allow HTTP requests with credentials
CORS(app, 
     origins=["*"],  # Will be overridden in before_request handler
     supports_credentials=True,  # Enable credentials support
     allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Cache-Control"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     expose_headers=["Content-Length", "X-JSON"],
     max_age=600)  # 10 minutes cache for preflight requests

# Register a before_request handler for CORS
@app.before_request
def handle_preflight():
    """Special handling for CORS preflight requests"""
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        
        # Get origin from the request headers
        origin = request.headers.get('Origin', '*')
        
        # Set the specific origin instead of wildcard to enable credentials
        response.headers['Access-Control-Allow-Origin'] = origin
        
        # Enable credentials support
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin, Cache-Control'
        response.headers['Access-Control-Max-Age'] = '600'  # Cache preflight response for 10 minutes
        
        return response

# Add after_request handler to set CORS headers for all responses
@app.after_request
def add_cors_headers(response):
    """Add CORS headers to all responses"""
    origin = request.headers.get('Origin')
    if origin:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    
    return response

# Add CORS test endpoint for debugging
@app.route('/cors-test', methods=['GET', 'OPTIONS'])
def cors_test():
    """Test endpoint for CORS configuration"""
    if request.method == 'OPTIONS':
        # Let the before_request handler handle this
        return app.make_default_options_response()
    
    # The response will have CORS headers added by the after_request handler
    return jsonify({
        "message": "CORS test successful",
        "your_origin": request.headers.get('Origin', 'No origin header'),
        "request_protocol": request.headers.get('X-Forwarded-Proto', 'http'),
        "request_headers": dict(request.headers),
        "cors_enabled": True,
        "cors_mode": "HTTP with credentials enabled",
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
        
        # Start background services
        start_notification_monitor()
        
        # Notify of server start
        emit_notification({'system': 'Server started successfully', 'event_type': 'server_start'})
        logging.info("Background services initialized")
    
    except Exception as e:
        logging.error(f"Background services error: {str(e)}")

# === Main Execution ===
if __name__ == "__main__":
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'true').lower() == 'true',
        use_reloader=True
    )