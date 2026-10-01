"""Gunicorn configuration. Every value can be overridden with an environment variable."""

import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# TensorFlow is memory-hungry and a model copy lives in every worker process,
# so prefer few workers with several threads.
workers = int(os.environ.get("WEB_CONCURRENCY", "1"))
threads = int(os.environ.get("GUNICORN_THREADS", "4"))
worker_class = "gthread"
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "60"))
graceful_timeout = 30
keepalive = 5
max_requests = 1000  # recycle workers periodically to bound memory growth
max_requests_jitter = 100

accesslog = "-"
errorlog = "-"


def post_worker_init(worker):
    """Load the model before the worker takes traffic so the first request isn't slow.

    If the model file is missing or broken this raises and the worker fails fast.
    """
    from core.ml import get_model

    get_model()
