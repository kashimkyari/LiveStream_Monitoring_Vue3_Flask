#!/usr/bin/env python3
"""
main.py - Flask application entry point
"""
import gevent.monkey
gevent.monkey.patch_all()

import logging
import os
from dotenv import load_dotenv
from flask import jsonify
from werkzeug.security import generate_password_hash
import secrets
import string
from config import create_app, configure_ssl_context
from extensions import db, socketio
from models import User

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize Flask app
app = create_app()

# Database initialization
def initialize_database():
    """Initialize database and create default admin user."""
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables initialized")
            admin_exists = User.query.filter_by(role='admin').first()
            if not admin_exists:
                admin_username = os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')
                admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD')
                admin_email = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@example.com')
                if not admin_password:
                    chars = string.ascii_letters + string.digits + string.punctuation
                    admin_password = ''.join(secrets.choice(chars) for _ in range(16))
                    logger.warning(f"Admin password not found. Generated: {admin_password}")
                    logger.warning("SAVE THIS PASSWORD AND SET ENV VARIABLES!")
                admin_user = User(
                    username=admin_username,
                    password=generate_password_hash(admin_password),
                    role='admin',
                    email=admin_email,
                    receive_updates=True
                )
                db.session.add(admin_user)
                db.session.commit()
                logger.info("Default admin user created")
            else:
                logger.info("Admin user already exists")
        except Exception as e:
            logger.error(f"DB init failed: {str(e)}")
            raise

# Main execution
if __name__ == "__main__":
    try:
        initialize_database()
        ssl_context = configure_ssl_context()
        server_mode = "HTTPS" if ssl_context else "HTTP"
        debug_mode = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
        logger.info(f"Starting server in {server_mode} mode with debug={'enabled' if debug_mode else 'disabled'}")
        
        socketio_kwargs = {
            'app': app,
            'host': '0.0.0.0',
            'port': int(os.getenv('PORT', 5000)),
            'debug': debug_mode,
            'use_reloader': debug_mode,
            'allow_unsafe_werkzeug': True
        }
        if ssl_context:
            socketio_kwargs['ssl_context'] = ssl_context

        socketio.run(**socketio_kwargs)
    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")
        raise