#!/usr/bin/env bash
set -euo pipefail

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Starting Gunicorn..."
exec gunicorn es_locator.wsgi:application -c /app/gunicorn.conf.py
