# app.py
from config import create_app
import os

app, socketio = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    # Run with socketio instead of app.run()
    socketio.run(app, host='0.0.0.0', port=port, debug=True, allow_unsafe_werkzeug=True)