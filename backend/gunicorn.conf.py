import multiprocessing
import os

# SSL Configuration
enable_ssl = os.getenv('ENABLE_SSL', 'true').lower() == 'true'
if enable_ssl:
    cert_dir = os.getenv('CERT_DIR', '/home/ec2-user/LiveStream_Monitoring_Vue3_Flask/backend')
    certfile = os.getenv('SSL_CERT_PATH', os.path.join(cert_dir, 'fullchain.pem'))
    keyfile = os.getenv('SSL_KEY_PATH', os.path.join(cert_dir, 'privkey.pem'))
    
    # SSL Context for Gunicorn
    keyfile = keyfile
    certfile = certfile
    
    # Log SSL configuration
    import logging
    logging.info(f"SSL Enabled with cert: {certfile} and key: {keyfile}")

# Binding & Protocol
if enable_ssl:
    bind = "0.0.0.0:5000 ssl"
else:
    bind = "0.0.0.0:5000"
protocol = "gevent"

# Worker Configuration
worker_class = "gevent"

# Calculate optimal number of workers based on available CPU cores
# Using a modified formula that balances speed and resource usage
cpu_count = multiprocessing.cpu_count()
workers = 4  # Cap at 12 for most environments

# Thread configuration - lower for gevent since it's async
threads = 4

# Connection settings
worker_connections = 2000
backlog = 2048  # Larger backlog for high-traffic scenarios

# Performance optimizations
max_requests = 1000  # Restart workers after handling this many requests
max_requests_jitter = 200  # Add randomness to prevent all workers restarting at once
preload_app = True  # Preload application code before forking workers
reuse_port = True  # Enable SO_REUSEPORT for faster restarts

# Timeouts (in seconds)
timeout = 30  # Reduced from 90 for faster error recovery
graceful_timeout = 15  # Reduced for faster restart cycles
keepalive = 5  # Lowered to free up connections faster

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"  # Log to stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s'
capture_output = True  # Capture stdout/stderr from workers

# Security Headers
forwarded_allow_ips = "*"
proxy_protocol = True
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# Statsd monitoring (uncomment and configure if you have statsd)
# statsd_host = "localhost:8125"
# statsd_prefix = "livestream_api"

# Immediately restart workers if they use too much memory
def worker_int(worker):
    worker.log.info("Worker received INT or QUIT signal")
    
    # Get the current process ID
    pid = os.getpid()
    worker.log.info("Worker syncing to disk before exit (pid: %s)", pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    pass

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")