import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from extensions import db, migrate
from utils.notifications import init_socketio

# ─── Load environment variables ───────────────────────────────────────
load_dotenv()

class Config:
    """Base configuration for all environments."""
    # ─── Secret & Security ───────────────────────────────────────────────
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'please-set-a-secure-key')
    SESSION_COOKIE_SECURE = True             # Only over HTTPS
    REMEMBER_COOKIE_SECURE = True            # Only over HTTPS

    # ─── Database ────────────────────────────────────────────────────────
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        raise RuntimeError('DATABASE_URL environment variable is required')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL   # Use only DATABASE_URL  
    SQLALCHEMY_TRACK_MODIFICATIONS = False   # Disable event system for performance

    # ─── CORS ────────────────────────────────────────────────────────────
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_ORIGINS = os.getenv(
        'CORS_ORIGINS',
        'http://localhost:5173,'
        'http://localhost:3000,'
        'https://live-stream-monitoring-vue3-flask.vercel.app'
    )  # ⚠️ In prod, override with explicit list via env var

def create_app(config_class=Config):
    """
    Application factory.
    Usage: app = create_app()
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # ─── Ensure instance folder exists ───────────────────────────────────
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError as e:
        app.logger.warning(f"Could not create instance path: {e}")  # Non-fatal

    # ─── CORS Setup ─────────────────────────────────────────────────────
    CORS(
        app,
        supports_credentials=app.config['CORS_SUPPORTS_CREDENTIALS'],
        origins=[origin.strip() for origin in app.config['CORS_ORIGINS'].split(',')]
    )

    # ─── Initialize Extensions ───────────────────────────────────────────
    try:
        db.init_app(app)         # SQLAlchemy
        migrate.init_app(app, db)  # Flask-Migrate
        
    except Exception as e:
        app.logger.error(f"Extension init failed: {e}")
        raise

    # ─── Initialize Socket.IO ───────────────────────────────────────────
    # Uses threading by default; swap to eventlet/gevent for scale
    socketio = init_socketio(app)

    # ─── Register Blueprints ─────────────────────────────────────────────
    from routes.auth_routes import auth_bp
    from routes.agent_routes import agent_bp
    from routes.stream_routes import stream_bp
    from routes.assignment_routes import assignment_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.detection_routes import detection_bp
    from routes.health_routes import health_bp
    from routes.keyword_object_routes import keyword_bp
    from routes.messaging_routes import messaging_bp
    from routes.notification_routes import notification_bp
    from routes.telegram_routes import telegram_bp

    for bp in (
        auth_bp, agent_bp, stream_bp, assignment_bp, dashboard_bp,
        detection_bp, health_bp, keyword_bp, messaging_bp, notification_bp,
        telegram_bp
    ):
        app.register_blueprint(bp)

    # ─── Error Handlers ─────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Not Found"}, 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.exception(error)
        return {"error": "Internal Server Error"}, 500

    # ─── Logging ─────────────────────────────────────────────────────────
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler

        if not os.path.isdir('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler(
            'logs/app.log', maxBytes=10240, backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Application startup')

    return app
