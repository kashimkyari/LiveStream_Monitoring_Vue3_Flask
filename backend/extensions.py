from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor

db = SQLAlchemy()
migrate = Migrate()

# Configure executors with larger pool size and proper shutdown
executors = {
    'default': ThreadPoolExecutor(20)  # Increase thread pool size
}

# Create scheduler with better configuration
scheduler = BackgroundScheduler(
    executors=executors,
    job_defaults={
        'coalesce': False,
        'max_instances': 3,
        'misfire_grace_time': 30
    }
)

def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)