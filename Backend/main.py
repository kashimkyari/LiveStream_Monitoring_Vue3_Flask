#!/usr/bin/env python3
"""
main.py - Flask application entry point with SSL support.

This application is configured to load SSL certificates if enabled via environment variables,
ensuring secure communication over HTTPS.
"""

import logging
import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Import application components
from config import create_app
from extensions import db
from models import User
from routes import *
from cleanup import start_chat_cleanup_thread, start_detection_cleanup_thread
from monitoring import start_notification_monitor

# Load environment variables from .env file
load_dotenv()

# Create the Flask app using a factory function
app = create_app()

# Configure CORS from environment variables
allowed_origins = os.getenv('ALLOWED_ORIGINS', 'https://live-stream-monitoring-vue3-flask.vercel.app').split(',')
CORS(app, supports_credentials=True, origins=allowed_origins)

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# Database initialization and default user creation
with app.app_context():
    try:
        # Initialize all database tables
        db.create_all()
        logging.info("Database tables initialized")

        # Create a default admin user if one doesn't exist
        admin_password = os.getenv('DEFAULT_ADMIN_PASSWORD')
        if not User.query.filter_by(role="admin").first() and admin_password:
            admin = User(
                username=os.getenv('DEFAULT_ADMIN_USERNAME', 'admin'),
                password=admin_password,
                role="admin",
            )
            db.session.add(admin)
            db.session.commit()
            logging.info("Default admin user created")

        # Create a default agent user if one doesn't exist
        agent_password = os.getenv('DEFAULT_AGENT_PASSWORD')
        if not User.query.filter_by(role="agent").first() and agent_password:
            agent = User(
                username=os.getenv('DEFAULT_AGENT_USERNAME', 'agent'),
                password=agent_password,
                role="agent",
            )
            db.session.add(agent)
            db.session.commit()
            logging.info("Default agent user created")

    except Exception as e:
        logging.error("Database initialization failed: %s", str(e))
        raise

# Start background tasks with error handling
try:
    start_notification_monitor()
    start_detection_cleanup_thread()
    logging.info("Background services started")
except Exception as e:
    logging.error("Failed to start background services: %s", str(e))

if __name__ == "__main__":
    # Determine debug mode from environment variables
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

    # Check if SSL should be enabled (production usage)
    # Set ENABLE_SSL=true in your environment variables to enable SSL.
    if os.getenv('ENABLE_SSL', 'false').lower() == 'true':
        # Use os.path.expanduser to correctly resolve '~' to the user's home directory.
        cert_dir = os.path.expanduser(os.getenv('CERT_DIR', '~/certs'))
        # Specify the SSL certificate and private key file names.
        ssl_cert = os.path.join(cert_dir, 'fullchain.pem')
        ssl_key = os.path.join(cert_dir, 'privkey.pem')
        
        # Verify that the certificate and key files exist before proceeding.
        if not (os.path.exists(ssl_cert) and os.path.exists(ssl_key)):
            logging.error("SSL certificates not found in %s", cert_dir)
            raise FileNotFoundError("SSL certificate files are missing")

        ssl_context = (ssl_cert, ssl_key)
        logging.info("SSL context is enabled using cert: %s and key: %s", ssl_cert, ssl_key)
    else:
        ssl_context = None
        logging.info("SSL context is disabled; running without SSL")

    # Run the Flask application.
    # Note: In production, consider using a WSGI server (e.g., Gunicorn) to better handle SSL and performance.
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        threaded=True,
        debug=debug_mode,
        ssl_context=ssl_context  # Use SSL context if available
    )
