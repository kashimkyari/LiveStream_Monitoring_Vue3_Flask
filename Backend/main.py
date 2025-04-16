#!/usr/bin/env python3
"""
main.py - Flask application entry point with SSL support and robust CORS.
"""

import logging
import os
from flask import Flask, request
from dotenv import load_dotenv

from config import create_app
from extensions import db
from models import User
from routes import *
from cleanup import start_chat_cleanup_thread, start_detection_cleanup_thread
from monitoring import start_notification_monitor

load_dotenv()
app = create_app()

# Allowed frontends (comma‑separated in .env)
ALLOWED_ORIGINS = os.getenv(
    'ALLOWED_ORIGINS',
    'https://live-stream-monitoring-vue3-flask.vercel.app'
).split(',')

# === Dynamic CORS Handler ===
@app.after_request
def apply_cors(response):
    origin = request.headers.get('Origin')
    if origin in ALLOWED_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
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

with app.app_context():
    try:
        db.create_all()
        logging.info("Database tables initialized")
        # create default users… (unchanged)
    except Exception as e:
        logging.error("DB init failed: %s", e)
        raise

try:
    start_notification_monitor()
    start_detection_cleanup_thread()
    logging.info("Background services started")
except Exception as e:
    logging.error("Background services failed: %s", e)

if __name__ == "__main__":
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
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
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=debug, ssl_context=ssl_ctx)
