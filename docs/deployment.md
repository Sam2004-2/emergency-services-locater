# Deployment Checklist

## Local Environment

1. Create virtualenv and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy environment template and adjust credentials as needed:
   ```bash
   cp .env.example .env
   ```
3. Create database and enable PostGIS extension:
   ```bash
   createdb es_locator
   psql -d es_locator -c "CREATE EXTENSION IF NOT EXISTS postgis;"
   psql -d es_locator -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
   ```
4. Apply Django migrations, collect static assets, and create an admin user:
   ```bash
   python manage.py migrate --noinput
   python manage.py collectstatic --noinput
   python manage.py createsuperuser
   ```
5. Import data from OpenStreetMap API (optional):
   ```bash
   python manage.py import_counties
   python manage.py import_facilities
   ```
6. Run the development server and browse to `http://127.0.0.1:8000/`:
   ```bash
   python manage.py runserver
   ```

## Docker Compose Stack

1. Copy environment template and tailor values:
   ```bash
   cp .env.example .env
   ```
2. Build and launch the full stack (PostGIS, Django/Gunicorn, Nginx, PgAdmin):
   ```bash
   docker compose up --build
   ```
3. Access the services:
   - App UI: <http://localhost/>
   - Django admin: <http://localhost/admin/>
   - PgAdmin: <http://localhost:5050/>
4. Stop or reset the stack:
   ```bash
   docker compose down          # preserve database volume
   docker compose down -v       # drop everything (full reset)
   ```

## Post-Deploy Health Checks

- `GET /api/facilities/?limit=1` returns HTTP 200 with GeoJSON data
- `GET /api/facilities/nearest?lat=53.3498&lon=-6.2603&limit=3` responds with ≤3 features
- `GET /api/counties/` returns county features (GeoJSON)
- Frontend map loads tiles, controls respond, and markers render
- Admin area reachable; login succeeds with test credentials
- `docker ps` reports healthy containers; Nginx access logs show HTTP 200s

## Troubleshooting

- **Ports busy**: adjust exposed ports (`5432`, `80`, `5050`) in `docker-compose.yml` or stop local services
- **Schema errors**: rerun Django migrations with `python manage.py migrate` to recreate tables and indexes
- **Missing static files**: ensure `python manage.py collectstatic` has run and the `staticfiles` volume is mounted for Nginx
- **API import failures**: check network connectivity and OpenStreetMap API rate limits; imports are rate-limited automatically
- **CSRF/hosts**: update `.env` with `DJANGO_ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` when deploying behind different domains
