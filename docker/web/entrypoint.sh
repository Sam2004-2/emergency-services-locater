#!/usr/bin/env bash
set -euo pipefail

# Collect static files
python manage.py collectstatic --noinput

# Apply database migrations (creates schema and indexes)
python manage.py migrate --noinput || true

# Start Gunicorn server
exec gunicorn es_locator.wsgi:application -c /app/gunicorn.conf.py
