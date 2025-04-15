import os
import logging
from dotenv import load_dotenv
from flask_cors import CORS

from config import create_app
from extensions import db
from models import User
from routes import *
from cleanup import start_chat_cleanup_thread, start_detection_cleanup_thread
from monitoring import start_notification_monitor

# Load environment variables
load_dotenv()

# Create the Flask app
app = create_app()

# Configure CORS from environment variables
allowed_origins = os.getenv('ALLOWED_ORIGINS', 'https://live-stream-monitoring-vue3-flask.vercel.app').split(',')
CORS(app, supports_credentials=True, origins=allowed_origins)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# Initialize the database and create default users within the app context
with app.app_context():
    try:
        db.create_all()
        logging.info("Database tables initialized")

        # Create default admin user if not exists
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

        # Create default agent user if not exists
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

# Conditionally start background tasks only if not running in a Vercel serverless environment.
# Vercel sets the "VERCEL" environment variable, so we skip starting persistent background threads.
if not os.getenv("VERCEL"):
    try:
        start_notification_monitor()
        start_detection_cleanup_thread()
        # Uncomment the next line if you want to enable chat cleanup in your local environment.
        # start_chat_cleanup_thread()
        logging.info("Background services started")
    except Exception as e:
        logging.error("Failed to start background services: %s", str(e))
else:
    logging.info("Skipping background services in Vercel environment")

# Export the Flask app as "handler" for Vercel to recognize your entry point.
handler = app

# Run the development server if executed locally
if __name__ == "__main__":
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        threaded=True,
        debug=debug_mode
    )
