#!/usr/bin/env python3
"""
main.py - Flask application entry point with SSL support and Socket.IO integration
"""

import logging
import os
import ssl
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash
import secrets
import string

# Import after Flask app creation
from config import create_app
from extensions import db
from models import User, Stream
from routes import *
from cleanup import start_chat_cleanup_thread, start_detection_cleanup_thread
from monitoring import start_notification_monitor
from flask_socketio import SocketIO

load_dotenv()

# Initialize Flask app FIRST
app = create_app()

# Configure Socket.IO ONCE
socketio = SocketIO(
    app,
    cors_allowed_origins=os.getenv('ALLOWED_ORIGINS', '*').split(','),
    path="/ws",
    async_mode='gevent',  # ✅ Required for production
    logger=True,
    engineio_logger=False
)

# === CORS Configuration ===
@app.after_request
def apply_cors(response):
    origin = request.headers.get('Origin', 'https://live-stream-monitoring-vue3-flask.vercel.app')
    if origin in os.getenv('ALLOWED_ORIGINS', '').split(','):
        response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-Requested-With'
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
    
        register_socket_events(socketio)
        start_notification_monitor()
        start_detection_cleanup_thread()
        emit_notification({'system': 'Server started successfully'})
    
    except Exception as e:
        logging.error(f"Background services error: {str(e)}")

# === SSL Context Creation ===
def create_ssl_context():
    cert_dir = os.path.expanduser(os.getenv('CERT_DIR', '/home/ec2-user/certs'))
    ssl_cert = os.path.join(cert_dir, 'fullchain.pem')
    ssl_key = os.path.join(cert_dir, 'privkey.pem')
    
    if not all([os.path.exists(ssl_cert), os.path.exists(ssl_key)]):
        raise FileNotFoundError(f"Missing SSL certs in {cert_dir}")
    
    context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(ssl_cert, ssl_key)
    return context

# === Main Execution ===
if __name__ == "__main__":
    ssl_ctx = create_ssl_context() if os.getenv('ENABLE_SSL', 'false').lower() == 'true' else None
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true',
        use_reloader=False,
        ssl_context=ssl_ctx
    )