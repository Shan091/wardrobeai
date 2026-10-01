#!/bin/sh
set -e

# Apply database migrations, then hand over to the main process (gunicorn by default).
python manage.py migrate --noinput

exec "$@"
