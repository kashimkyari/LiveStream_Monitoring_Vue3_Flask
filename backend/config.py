import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from extensions import db
from services.notification_service import NotificationService

load_dotenv()

class Config:
    """Base configuration for all environments."""
    # ─── Secret & Security ───────────────────────────────────────────────
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'please-set-a-secure-key')
    SESSION_COOKIE_SECURE = os.getenv('ENABLE_SSL', 'false').lower() == 'true'
    REMEMBER_COOKIE_SECURE = os.getenv('ENABLE_SSL', 'false').lower() == 'true'

    # ─── Database ────────────────────────────────────────────────────────
    if os.getenv('DATABASE_URL') and 'supabase' in os.getenv('DATABASE_URL'):
        db_uri = os.getenv('DATABASE_URL')
        masked_uri = db_uri[:db_uri.find('://') + 3] + '****:****@' + db_uri[db_uri.find('@') + 1:]
        print(f"Using Supabase database: {masked_uri}")
        
        # Handle SSL parameters
        ssl_params = []
        if 'sslmode' not in db_uri:
            ssl_params.append('sslmode=require')
        
        root_cert_path = os.getenv('PG_ROOT_CERT_PATH')
        if root_cert_path and os.path.exists(root_cert_path):
            print(f"Using SSL root certificate: {root_cert_path}")
            ssl_params.append(f'sslrootcert={root_cert_path}')
        else:
            print("Using SSL without certificate verification")
            if 'sslmode' not in db_uri:
                ssl_params.append('sslmode=require')
        
        if ssl_params:
            connector = '&' if '?' in db_uri else '?'
            db_uri = f"{db_uri}{connector}{'&'.join(ssl_params)}"
        
        SQLALCHEMY_DATABASE_URI = db_uri
    else:
        SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'max_overflow': 2,
        'connect_args': {
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5
        }
    }

    # ─── CORS ────────────────────────────────────────────────────────────
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'https://monitor.jetcamstudio.com,*')

    # ─── Monitoring Intervals ────────────────────────────────────────────
    STREAM_STATUS_CHECK_INTERVAL = int(os.getenv('STREAM_STATUS_CHECK_INTERVAL', 60))
    VIEWER_COUNT_INTERVAL = int(os.getenv('VIEWER_COUNT_INTERVAL', 30))
    NOTIFICATION_DEBOUNCE = int(os.getenv('NOTIFICATION_DEBOUNCE', 300))

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = config_class.SQLALCHEMY_ENGINE_OPTIONS
    app.config['CONTINUOUS_MONITORING'] = os.getenv('CONTINUOUS_MONITORING', 'true').lower() == 'true'
    app.config['ENABLE_AUDIO_MONITORING'] = os.getenv('ENABLE_AUDIO_MONITORING', 'true').lower() == 'true'
    app.config['ENABLE_VIDEO_MONITORING'] = os.getenv('ENABLE_VIDEO_MONITORING', 'true').lower() == 'true'
    app.config['ENABLE_CHAT_MONITORING'] = os.getenv('ENABLE_CHAT_MONITORING', 'true').lower() == 'true'
    app.config['CHAT_ALERT_COOLDOWN'] = int(os.getenv('CHAT_ALERT_COOLDOWN', 60))
    app.config['VISUAL_ALERT_COOLDOWN'] = int(os.getenv('VISUAL_ALERT_COOLDOWN', 60))
    app.config['AUDIO_ALERT_COOLDOWN'] = int(os.getenv('AUDIO_ALERT_COOLDOWN', 60))
    app.config['NEGATIVE_SENTIMENT_THRESHOLD'] = float(os.getenv('NEGATIVE_SENTIMENT_THRESHOLD', -0.5))
    app.config['WHISPER_MODEL_SIZE'] = os.getenv('WHISPER_MODEL_SIZE', 'base')

    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError as e:
        app.logger.warning(f"Could not create instance path: {e}")

    # ─── CORS Setup ─────────────────────────────────────────────────────
    CORS(
        app,
        supports_credentials=app.config['CORS_SUPPORTS_CREDENTIALS'],
        origins=[u.strip() for u in app.config['CORS_ORIGINS'].split(',')],
        resources={r"/api/*": {}, r"/socket.io/*": {}}
    )

    # ─── Initialize Extensions ───────────────────────────────────────────
    try:
        db.init_app(app)
    except Exception as e:
        app.logger.error(f"Database init failed: {e}")
        raise

    # ─── Initialize Notification Service ────────────────────────────────
    with app.app_context():
        try:
            NotificationService.init(app)
            NotificationService.start_scheduler()
            app.logger.info("Notification service initialized")
        except Exception as e:
            app.logger.error(f"Notification service init failed: {e}")
            raise

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