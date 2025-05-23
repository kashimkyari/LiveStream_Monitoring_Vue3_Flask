#!/usr/bin/env python3
"""
monitor_app.py - Standalone Flask application for livestream monitoring
"""
import gevent.monkey
gevent.monkey.patch_all()

import logging
import os
from dotenv import load_dotenv
from config import create_app, configure_ssl_context
from extensions import db, socketio
from monitoring import start_notification_monitor, initialize_monitoring
from routes.monitor_routes import monitor_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize Flask app with monitor blueprint
app = create_app(blueprint=monitor_bp)
app.config['PORT'] = int(os.getenv('MONITOR_PORT', 5001))

# Main execution
if __name__ == "__main__":
    try:
        ssl_context = configure_ssl_context()
        server_mode = "HTTPS" if ssl_context else "HTTP"
        debug_mode = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
        logger.info(f"Starting monitoring server in {server_mode} mode with debug={'enabled' if debug_mode else 'disabled'}")

        with app.app_context():
            db.create_all()
            logger.info("Database tables initialized")
            # Initialize monitoring for detection-related alerts only
            initialize_monitoring()
            start_notification_monitor()
            logger.info("Started monitoring for detection-related alerts (audio, video, chat)")

        socketio_kwargs = {
            'app': app,
            'host': '0.0.0.0',
            'port': app.config['PORT'],
            'debug': debug_mode,
            'use_reloader': debug_mode,
            'allow_unsafe_werkzeug': True
        }
        if ssl_context:
            socketio_kwargs['ssl_context'] = ssl_context

        socketio.run(**socketio_kwargs)
    except Exception as e:
        logger.error(f"Monitoring application startup failed: {str(e)}")
        raise