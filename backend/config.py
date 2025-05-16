import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from extensions import db
from utils.notifications import init_socketio

# Load .env into environment (must be in project root)
load_dotenv()

class Config:
    """Base configuration for all environments."""
    # ─── Secret & Security ───────────────────────────────────────────────
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'please-set-a-secure-key')
    SESSION_COOKIE_SECURE = False            # Allow cookies over HTTP?
    REMEMBER_COOKIE_SECURE = False           # Allow cookies over HTTP

    # ─── Database ────────────────────────────────────────────────────────
    # For Supabase or other hosted PostgreSQL services, ensure SSL is configured
    if os.getenv('DATABASE_URL') and 'supabase' in os.getenv('DATABASE_URL'):
        # Log the database URI (mask sensitive parts)
        db_uri = os.getenv('DATABASE_URL')
        masked_uri = db_uri[:db_uri.find('://') + 3] + '****:****@' + db_uri[db_uri.find('@') + 1:]
        print(f"Using Supabase database: {masked_uri}")
        
        # Check if sslmode is already in the URI
        if 'sslmode' not in db_uri:
            db_uri = f"{db_uri}?sslmode=verify-ca"
        
        # Set the SSL root certificate path
        root_cert_path = os.getenv('PG_ROOT_CERT_PATH')
        if root_cert_path and os.path.exists(root_cert_path):
            print(f"Using SSL root certificate: {root_cert_path}")
            SQLALCHEMY_DATABASE_URI = f"{db_uri}&sslrootcert={root_cert_path}"
        else:
            print(f"SSL root certificate not found at: {root_cert_path}. Attempting connection without it.")
            SQLALCHEMY_DATABASE_URI = db_uri
    else:
        SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False   # Disable event system for performance

    # ─── CORS ────────────────────────────────────────────────────────────
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')

def create_app(config_class=Config):
    # Create app with instance folder for config & SQLite file
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError as e:
        app.logger.warning(f"Could not create instance path: {e}")

    # ─── CORS Setup ─────────────────────────────────────────────────────
    CORS(
        app,
        supports_credentials=app.config['CORS_SUPPORTS_CREDENTIALS'],
        origins=[u.strip() for u in app.config['CORS_ORIGINS'].split(',')]
    )

    # ─── Initialize Extensions ───────────────────────────────────────────
    try:
        db.init_app(app)                     # SQLAlchemy
    except Exception as e:
        app.logger.error(f"Extension init failed: {e}")
        raise

    # ─── Initialize Socket.IO ───────────────────────────────────────────
    with app.app_context():  # Add app context here
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

    for bp in (
        auth_bp, agent_bp, stream_bp, assignment_bp, dashboard_bp,
        detection_bp, health_bp, keyword_bp, messaging_bp, notification_bp
    ):
        app.register_blueprint(bp)

    # ─── Error Handlers ─────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(err):
        return {"error": "Not Found"}, 404

    @app.errorhandler(500)
    def server_error(err):
        app.logger.exception(err)
        return {"error": "Internal Server Error"}, 500

    return app