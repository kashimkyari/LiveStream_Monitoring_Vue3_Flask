import multiprocessing

# Binding
bind = "0.0.0.0:5000"

# Worker configuration
worker_class = "threads"
workers = multiprocessing.cpu_count() * 2 + 1
threads = 4

# Timeouts
timeout = 120
graceful_timeout = 30
keepalive = 5

# Performance tuning
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Logging
loglevel = "info"
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
capture_output = True

# SSL configuration
certfile = "./fullchain.pem"
keyfile = "./privkey.pem"
# Note: Don't create the SSL context object here
# Just specify the cert and key files

# Process naming
proc_name = "livestream-monitoring"

# Preload app for better performance
preload_app = True