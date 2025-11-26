#!/usr/bin/env bash
set -euo pipefail

echo "=== Emergency Services Locator - Starting ==="

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# Apply database migrations
echo "🗄️ Applying database migrations..."
python manage.py migrate --noinput

# Check if seeding is requested via environment variable
if [ "${SEED_DATABASE:-false}" = "true" ] || [ "${SEED_DATABASE:-false}" = "1" ]; then
    echo "🌱 Seeding database from OpenStreetMap APIs..."
    python manage.py seed_database --clear
fi

echo "�� Starting Gunicorn server..."
exec gunicorn es_locator.wsgi:application -c /app/gunicorn.conf.py
