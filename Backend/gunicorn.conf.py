import multiprocessing

bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
threads = 2
timeout = 60
loglevel = "info"
certfile = "/home/ec2-user/certs/fullchain.pem"  # Update path
keyfile = "/home/ec2-user/certs/privkey.pem"     # Update path
ssl_version = "TLSv1_2"