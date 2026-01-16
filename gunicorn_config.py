# Gunicorn configuration file
import sys
import re

# Worker processes
workers = 3
worker_class = 'sync'
timeout = 120
bind = '0.0.0.0:8000'

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Access log format - we'll filter health checks in middleware instead
access_log_format = '%(h)s - %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("🚀 Starting Gunicorn server...")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("🔄 Reloading Gunicorn server...")

def worker_int(worker):
    """Called when a worker receives the INT or QUIT signal."""
    worker.log.info("⚠️ Worker received INT or QUIT signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"✅ Worker spawned (pid: {worker.pid})")

def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("🔄 Forking new master process...")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("✅ Gunicorn server is ready. Spawning workers...")

def worker_abort(worker):
    """Called when a worker receives the ABRT signal."""
    worker.log.warning("⚠️ Worker received ABRT signal")

