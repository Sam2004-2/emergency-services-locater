#!/usr/bin/env bash
set -euo pipefail

python manage.py collectstatic --noinput
python manage.py migrate --noinput || true

export PGPASSWORD="${DB_PASS:-postgres}"
DB_URI="host=${DB_HOST:-localhost} port=${DB_PORT:-5432} dbname=${DB_NAME:-es_locator} user=${DB_USER:-postgres}"

# Apply database schema if tables don't exist
if ! psql "$DB_URI" -c "SELECT 1 FROM emergency_facility LIMIT 1" >/dev/null 2>&1; then
  echo "Applying database schema..."
  psql "$DB_URI" -f db/schema/001_extensions.sql || true
  psql "$DB_URI" -f db/schema/010_bounds_counties.sql || true
  psql "$DB_URI" -f db/schema/020_services_facilities.sql || true
  psql "$DB_URI" -f db/schema/040_constraints_indexes.sql || true
  
  echo "Seeding initial data..."
  psql "$DB_URI" -f db/import/seed_counties.sql || true
  psql "$DB_URI" -f db/import/seed_facilities.sql || true
fi

exec gunicorn es_locator.wsgi:application -c /app/gunicorn.conf.py
