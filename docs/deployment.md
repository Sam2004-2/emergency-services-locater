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
3. Ensure PostgreSQL + PostGIS are running, then bootstrap schema and seed data:
   ```bash
   createdb es_locator
   psql -d es_locator -f db/schema/001_extensions.sql
   psql -d es_locator -f db/schema/010_bounds_counties.sql
   psql -d es_locator -f db/schema/020_services_facilities.sql
   psql -d es_locator -f db/schema/040_constraints_indexes.sql
   psql -d es_locator -f db/import/seed_facilities.sql
   ```
4. Apply Django migrations, collect static assets, and create an admin user:
   ```bash
   python manage.py migrate --noinput
   python manage.py collectstatic --noinput
   python manage.py createsuperuser
   ```
5. Run the development server and browse to `http://127.0.0.1:8000/`:
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
- **Schema errors**: rerun SQL scripts from `db/schema` to recreate tables and constraints
- **Missing static files**: ensure `python manage.py collectstatic` has run and the `staticfiles` volume is mounted for Nginx
- **SRID complaints**: confirm source data is reprojected to EPSG:4326 before import (`ogr2ogr -t_srs EPSG:4326`)
- **CSRF/hosts**: update `.env` with `DJANGO_ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` when deploying behind different domains
