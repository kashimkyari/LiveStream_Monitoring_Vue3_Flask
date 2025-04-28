import multiprocessing
import ssl

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

# SSL configuration - updated approach
certfile = "./fullchain.pem"
keyfile = "./privkey.pem"

# Create SSL context with modern protocols
ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(certfile, keyfile)
ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2

# Process naming
proc_name = "livestream-monitoring"

# Preload app for better performance
preload_app = True