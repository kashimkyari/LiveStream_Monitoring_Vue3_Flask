import multiprocessing

# Binding & Protocol
bind = "0.0.0.0:5000"
protocol = "gevent"  # Explicit protocol declaration

# Worker Configuration 
worker_class = "gevent"
# For I/O-bound apps, better formula:
workers = min(multiprocessing.cpu_count() * 2, 16) + 1  # Cap at 16 CPU cores
threads = 2  # Lower for gevent (since we're async)
worker_connections = 2000  # Increase for high concurrent connections

# Timeouts
timeout = 90  # Slightly shorter for faster recovery
graceful_timeout = 45  # Give more time for graceful shutdown
keepalive = 10  # Slightly higher for persistent connections

# Security Headers (add this section)
forwarded_allow_ips = "*"
proxy_protocol = True
limit_request_line = 8190  # Max size of HTTP request line