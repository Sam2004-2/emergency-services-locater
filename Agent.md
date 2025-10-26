Overview

The Emergency Services Locator is a location-based web application that enables users to discover nearby emergency services (e.g. hospitals, fire stations, Garda stations, ambulance bases) across Ireland, visualized on an interactive map.

The application will:

Import and manage spatial datasets of emergency facilities and administrative boundaries using PostGIS.

Provide RESTful API endpoints for querying services based on proximity, containment, and type.

Include a responsive, accessible front-end that visualizes the data via Leaflet JS and OpenStreetMap tiles.

Support spatial queries such as nearest facility, within radius, within county/polygon, and service coverage buffering.

Optionally support Dockerized deployment with isolated Django, PostGIS, PgAdmin, and Nginx services.

Initially, the focus is on the Republic of Ireland, but the design should allow easy generalization to any country with compatible datasets.

Learning Objectives

By completing this project, the AI agent should demonstrate and document the following outcomes:

Spatial Database Design

Create a normalized schema in PostgreSQL/PostGIS with appropriate spatial data types (Points, Polygons, and optionally Lines).

Implement GIST/BRIN indexes on geometry columns.

Populate data from open Irish datasets (or generated samples).

Spatial Query Implementation

Write and optimize at least 3 complex spatial SQL queries:

Proximity (find nearest/within radius)

Containment (within a county polygon)

Buffering/intersection (e.g. service coverage zones)

Demonstrate queries in both SQL and Django ORM.

Middle Tier – Django & REST API

Implement Django models linked to PostGIS tables.

Create RESTful API endpoints using Django REST Framework and rest_framework_gis.

Include data validation, error handling, and optional authentication.

Front-End – Leaflet & UI

Integrate Leaflet maps for spatial visualization.

Add user interactions (zoom, pan, filter by service type, “find nearest” button).

Design a responsive, accessible interface (Bootstrap 5 or similar).

Deployment & Security

Configure local deployment (with or without Docker).

Secure environment variables and apply production-style settings.

Document setup, run instructions, and test credentials.

Documentation & Testing

Generate a complete README with setup, architecture diagram, and screenshots.

Provide API documentation and a sample user guide.

Implement validation tests for data import, query results, and API responses.

Project Architecture Overview
Layer	Technology	Responsibilities
Database	PostgreSQL + PostGIS	Store and index spatial data; support geometry operations and queries.
Backend	Django + Django REST Framework + rest_framework_gis	Manage models, serializers, and REST endpoints for spatial queries.
Frontend	Bootstrap 5 + Leaflet JS + OpenStreetMap	Render interactive map, display facilities and user interactions.
Optional Deployment	Docker Compose + Nginx + PgAdmin	Multi-container setup for production-like deployment.
Dataset Plan

The AI should either import or programmatically generate the following datasets:

Dataset	Geometry Type	Example Fields	Source / Notes
Irish Counties	MultiPolygon	id, name_en, geom	OpenStreetMap / Townlands.ie shapefile
Emergency Facilities	Point	id, name, type (hospital/fire/police/ambulance), address, geom	Open Data (https://data.gov.ie
) or synthetic generation
Major Roads (optional)	LineString	id, road_name, road_type, geom	Optional for buffer/intersection queries

Each geometry column should use SRID 4326 (WGS84) for compatibility with Leaflet.
Spatial indexes (GIST) must be created for all geometry columns.

Planned Spatial Queries

The AI must implement and test the following minimum spatial operations:

Query Name	Type	SQL Example	Purpose
Find Nearest Service	Proximity (KNN)	ORDER BY geom <-> ST_SetSRID(ST_MakePoint(lon,lat),4326)	Find closest facility to user point
Within Radius	Proximity (ST_DWithin)	WHERE ST_DWithin(geom::geography, user_point, radius_m)	Get all facilities within X km
Within County	Containment	ST_Within(facility.geom, county.geom)	Filter facilities by administrative area
Service Coverage Buffer	Buffer/Intersection	ST_Buffer(facility.geom::geography, 10000)	Visualize 10km service coverage
Cross-layer Query (optional)	Intersection	ST_Intersects(facility.geom, road.geom)	Identify facilities near transport routes

Each query should be demonstrated via both:

A raw SQL file (for documentation and assessment)

A Django ORM equivalent method in a custom model manager

Planned Django Apps

The AI should organize the project into modular Django apps:

App Name	Responsibility
core	Project configuration, authentication, API root
services	Models, views, and API endpoints for emergency facilities
boundaries	Administrative boundaries (Irish counties)
frontend	Templates, Leaflet integration, UI components

Each app should follow clean MVC principles:

Models: Spatial data definitions + indexes

Views: REST endpoints and query handlers

Templates: HTML + JavaScript Leaflet views

Expected Deliverables

The AI must generate:

Database artifacts

SQL scripts for data import and index creation

At least three verified spatial queries

Output logs / screenshots of results

Django source code

All app directories with models, serializers, views, and URLs

REST API endpoints for CRUD + spatial queries

Static + template files for front-end

Documentation

README.md (features, setup, dependencies, screenshots, API endpoints)

Architecture diagram and database schema image

Query and performance documentation

Test credentials and example API usage

Deployment configuration

Local .env.example

docker-compose.yml (for bonus marks)

Nginx reverse proxy configuration (for Docker setup)

Next Section Preview

In Part 2, the AI agent will receive detailed step-by-step build instructions:

Project scaffolding

Database schema creation and spatial data import

Spatial query creation and verification scripts

Django model definitions and custom query managers


🧱 Part 2 — Database Layer & Spatial Data Management (PostgreSQL/PostGIS)
Agent Role & Success Criteria

You are the lead developer agent. Deliver a fully working PostGIS database for the Emergency Services Locator with:

A normalized schema using Point (facilities) and MultiPolygon (counties), optionally LineString (roads).

SRID 4326 consistently.

GIST indexes on all geometry columns; consider BRIN where sensible for large tables.

Verified spatial queries (proximity, containment, buffering/intersection) with EXPLAIN ANALYZE notes.

Repeatable import scripts and seed data so the app works on any machine.

Your outputs must include:

SQL migration/DDL files

Import scripts (ogr2ogr usage or Python/SQL loaders)

Verification SQL (counts, SRIDs, indexes, sample queries)

Brief performance notes (index usage confirmation)

2.1 Project & Data Folders

Create a consistent, repo-friendly structure (paths relative to repo root):

/db
  /schema
    001_extensions.sql
    010_bounds_counties.sql
    020_services_facilities.sql
    030_transport_roads.sql  (optional)
    040_constraints_indexes.sql
  /import
    import_counties.sh
    import_facilities.sh
    seed_facilities.sql
  /queries
    verify_basics.sql
    verify_spatial.sql
    performance_explain.sql
/spatial_data
  /boundaries
  /facilities
  /roads


Rule: All SQL in /db must be idempotent (safe to re-run) or guarded by IF NOT EXISTS semantics.

2.2 Database Bootstrap

Create a local database named es_locator (configurable via .env).

/db/schema/001_extensions.sql

-- Enable PostGIS and useful extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder; -- ok to skip if unavailable


Execution (example):

psql -h localhost -U $DB_USER -d es_locator -f db/schema/001_extensions.sql

2.3 Core Schema (Irish-first, generalisable)
2.3.1 Administrative Boundaries (Counties)

/db/schema/010_bounds_counties.sql

-- Administrative boundaries: Irish counties (generalizable to any country/region)
CREATE TABLE IF NOT EXISTS admin_counties (
  id SERIAL PRIMARY KEY,
  source_id TEXT,                       -- original dataset id (nullable)
  name_en TEXT NOT NULL,
  name_local TEXT,
  iso_code TEXT,                        -- optional code
  geom geometry(MULTIPOLYGON, 4326) NOT NULL
);

-- Spatial index
CREATE INDEX IF NOT EXISTS admin_counties_geom_gix
  ON admin_counties USING GIST (geom);

2.3.2 Emergency Facilities (Hospitals, Fire, Garda, Ambulance)

/db/schema/020_services_facilities.sql

-- Emergency facilities as Points
CREATE TYPE facility_type AS ENUM ('hospital', 'fire_station', 'police_station', 'ambulance_base');

CREATE TABLE IF NOT EXISTS emergency_facility (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  type facility_type NOT NULL,
  address TEXT,
  phone TEXT,
  website TEXT,
  properties JSONB DEFAULT '{}'::jsonb,  -- flexible metadata (e.g., A&E availability)
  geom geometry(POINT, 4326) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Last-modified trigger (optional but nice)
CREATE OR REPLACE FUNCTION touch_updated_at() RETURNS trigger AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS emergency_facility_touch ON emergency_facility;
CREATE TRIGGER emergency_facility_touch
BEFORE UPDATE ON emergency_facility
FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

-- Spatial + text search indexes
CREATE INDEX IF NOT EXISTS emergency_facility_geom_gix
  ON emergency_facility USING GIST (geom);
CREATE INDEX IF NOT EXISTS emergency_facility_name_trgm
  ON emergency_facility USING GIN ((name) gin_trgm_ops);


Note: If pg_trgm isn’t enabled, add CREATE EXTENSION IF NOT EXISTS pg_trgm; to 001_extensions.sql.

2.3.3 Optional: Major Roads (for buffer/intersection demos)

/db/schema/030_transport_roads.sql

CREATE TABLE IF NOT EXISTS major_road (
  id SERIAL PRIMARY KEY,
  road_name TEXT,
  road_type TEXT, -- e.g. motorway, national, regional
  geom geometry(LINESTRING, 4326) NOT NULL
);

CREATE INDEX IF NOT EXISTS major_road_geom_gix
  ON major_road USING GIST (geom);

2.3.4 Constraints & SRID Guards

/db/schema/040_constraints_indexes.sql

-- SRID enforcement and basic geometry sanity checks
ALTER TABLE emergency_facility
  ADD CONSTRAINT emergency_facility_srid_chk
  CHECK (ST_SRID(geom) = 4326);

ALTER TABLE admin_counties
  ADD CONSTRAINT admin_counties_srid_chk
  CHECK (ST_SRID(geom) = 4326);

-- Optional: ensure points really are points, multipolygons really are multipolygons
ALTER TABLE emergency_facility
  ADD CONSTRAINT emergency_facility_geomtype_chk
  CHECK (GeometryType(geom) = 'POINT');

ALTER TABLE admin_counties
  ADD CONSTRAINT admin_counties_geomtype_chk
  CHECK (GeometryType(geom) IN ('MULTIPOLYGON','POLYGON')); -- accept POLYGON; cast to MULTI later if needed

2.4 Data Import (Irish Focus)
2.4.1 Counties (Open Data / OSM-derived)

Input expectation: a counties shapefile/GeoPackage with polygons for Irish counties (WGS84 if possible; otherwise reproject).

/db/import/import_counties.sh

#!/usr/bin/env bash
set -euo pipefail

: "${DB_HOST:=localhost}"
: "${DB_PORT:=5432}"
: "${DB_NAME:=es_locator}"
: "${DB_USER:=postgres}"
: "${DB_PASS:=postgres}"
: "${SRC_FILE:=./spatial_data/boundaries/irish_counties.gpkg}"
: "${SRC_LAYER:=counties}"

export PGPASSWORD="$DB_PASS"

ogr2ogr -f "PostgreSQL" \
  PG:"host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=$DB_USER password=$DB_PASS" \
  "$SRC_FILE" "$SRC_LAYER" \
  -nln admin_counties \
  -overwrite \
  -lco GEOMETRY_NAME=geom \
  -lco FID=id \
  -nlt MULTIPOLYGON \
  -t_srs EPSG:4326


If your source is SHP: replace the SRC_FILE and remove the layer arg.

2.4.2 Facilities (Hospitals/Fire/Garda/Ambulance)

Prefer authoritative CSV/GeoJSON where available. If none is available during development, seed with a small high-quality sample (Dublin + regional capitals) so the app is demo-ready.

Option A — Import real GeoJSON (recommended):

/db/import/import_facilities.sh

#!/usr/bin/env bash
set -euo pipefail

: "${DB_HOST:=localhost}"
: "${DB_PORT:=5432}"
: "${DB_NAME:=es_locator}"
: "${DB_USER:=postgres}"
: "${DB_PASS:=postgres}"
: "${SRC_FILE:=./spatial_data/facilities/ireland_emergency_facilities.geojson}"

export PGPASSWORD="$DB_PASS"

# Load into a temp table to normalize types
ogr2ogr -f "PostgreSQL" \
  PG:"host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=$DB_USER password=$DB_PASS" \
  "$SRC_FILE" \
  -nln _tmp_facilities \
  -overwrite \
  -lco GEOMETRY_NAME=geom \
  -nlt POINT \
  -t_srs EPSG:4326

# Normalize into emergency_facility with controlled ENUM types
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<'SQL'
INSERT INTO emergency_facility (name, type, address, phone, website, properties, geom)
SELECT
  COALESCE(name, 'Unnamed'),
  CASE
    WHEN LOWER(category) LIKE '%hospital%'          THEN 'hospital'::facility_type
    WHEN LOWER(category) LIKE '%fire%'              THEN 'fire_station'::facility_type
    WHEN LOWER(category) LIKE '%police%' OR LOWER(category) LIKE '%garda%' THEN 'police_station'::facility_type
    WHEN LOWER(category) LIKE '%ambulance%'         THEN 'ambulance_base'::facility_type
    ELSE 'hospital'::facility_type -- default; adjust mapping
  END,
  address,
  phone,
  website,
  to_jsonb(row_to_json(t)) - 'geom'::text, -- keep original attrs (minus geometry) in properties
  geom
FROM _tmp_facilities t;
DROP TABLE IF EXISTS _tmp_facilities;
SQL


Option B — Seed minimal data (fast path):

/db/import/seed_facilities.sql

-- Minimal starter dataset (Dublin + a few regions)
INSERT INTO emergency_facility (name, type, address, geom)
VALUES
  ('St. James''s Hospital', 'hospital', 'Dublin 8', ST_SetSRID(ST_MakePoint(-6.2967, 53.3393),4326)),
  ('Mater Misericordiae University Hospital', 'hospital', 'Eccles St, Dublin 7', ST_SetSRID(ST_MakePoint(-6.2682, 53.3599),4326)),
  ('Dublin Fire Brigade HQ', 'fire_station', 'Townsend St, Dublin 2', ST_SetSRID(ST_MakePoint(-6.2526, 53.3453),4326)),
  ('Store St Garda Station', 'police_station', 'Store St, Dublin 1', ST_SetSRID(ST_MakePoint(-6.2521, 53.3507),4326)),
  ('National Ambulance Service – HQ', 'ambulance_base', 'Tallaght, Dublin 24', ST_SetSRID(ST_MakePoint(-6.3696, 53.2876),4326));


Execution examples:

psql -h localhost -U $DB_USER -d es_locator -f db/import/seed_facilities.sql

2.4.3 Optional: Roads

Use OSM-derived roads if available (GeoPackage/GeoJSON). Similar to counties import:

ogr2ogr -f "PostgreSQL" \
  PG:"host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=$DB_USER password=$DB_PASS" \
  ./spatial_data/roads/ireland_major_roads.gpkg roads \
  -nln major_road \
  -overwrite \
  -lco GEOMETRY_NAME=geom \
  -nlt LINESTRING \
  -t_srs EPSG:4326

2.5 Verification & Sanity Checks

Create /db/queries/verify_basics.sql:

-- Table existence & counts
SELECT 'admin_counties' AS table, COUNT(*) FROM admin_counties
UNION ALL
SELECT 'emergency_facility', COUNT(*) FROM emergency_facility
UNION ALL
SELECT 'major_road', COUNT(*) FROM major_road;

-- Geometry columns & SRIDs
SELECT f_table_name, f_geometry_column, srid, type
FROM geometry_columns
WHERE f_table_name IN ('admin_counties','emergency_facility','major_road');

-- Sample geometries
SELECT id, name, ST_AsText(geom) FROM emergency_facility LIMIT 5;

-- Index presence
SELECT
  t.relname AS table_name,
  i.relname AS index_name,
  am.amname AS index_type
FROM pg_class t
JOIN pg_index ix ON t.oid = ix.indrelid
JOIN pg_class i ON i.oid = ix.indexrelid
JOIN pg_am am ON i.relam = am.oid
WHERE t.relname IN ('admin_counties','emergency_facility','major_road')
ORDER BY t.relname;


Create /db/queries/verify_spatial.sql (these will be reused later by the API):

-- 1) Containment: facilities within each county
SELECT c.name_en AS county, COUNT(f.*) AS facilities
FROM admin_counties c
LEFT JOIN emergency_facility f
  ON ST_Within(f.geom, c.geom)
GROUP BY c.name_en
ORDER BY facilities DESC;

-- 2) Proximity (radius): facilities within 10km of a point (Dublin centric)
WITH user_point AS (
  SELECT ST_SetSRID(ST_MakePoint(-6.2603, 53.3498), 4326)::geography AS g
)
SELECT f.id, f.name, f.type,
       ST_Distance(f.geom::geography, (SELECT g FROM user_point)) AS meters
FROM emergency_facility f
WHERE ST_DWithin(f.geom::geography, (SELECT g FROM user_point), 10000)
ORDER BY meters ASC;

-- 3) Nearest-K (KNN): 5 nearest facilities to a point
SELECT id, name, type
FROM emergency_facility
ORDER BY geom <-> ST_SetSRID(ST_MakePoint(-6.2603, 53.3498), 4326)
LIMIT 5;

-- 4) Buffer & intersection (coverage): facilities whose 10 km buffers intersect a county
WITH buffers AS (
  SELECT id, name, type, ST_Buffer(geom::geography, 10000)::geometry AS buf
  FROM emergency_facility
)
SELECT c.name_en AS county, COUNT(b.id) AS facilities_covering
FROM admin_counties c
JOIN buffers b ON ST_Intersects(b.buf, c.geom)
GROUP BY c.name_en
ORDER BY facilities_covering DESC;


Create /db/queries/performance_explain.sql:

EXPLAIN ANALYZE
SELECT id, name
FROM emergency_facility
WHERE ST_DWithin(
  geom::geography,
  ST_SetSRID(ST_MakePoint(-6.2603, 53.3498), 4326)::geography,
  10000
);

EXPLAIN ANALYZE
SELECT id, name
FROM emergency_facility
ORDER BY geom <-> ST_SetSRID(ST_MakePoint(-6.2603, 53.3498), 4326)
LIMIT 10;


Run checks:

psql -h localhost -U $DB_USER -d es_locator -f db/queries/verify_basics.sql
psql -h localhost -U $DB_USER -d es_locator -f db/queries/verify_spatial.sql
psql -h localhost -U $DB_USER -d es_locator -f db/queries/performance_explain.sql


Record results (paste into /docs/db_verification.md) and note:

Counts > 0

SRID 4326 confirmed

GIST indexes present

EXPLAIN ANALYZE shows Index Scan or KNN usage where expected

2.6 Data Hygiene & Topology (Optional but Good for Marks)

Add a quick validity scan:

-- Invalid county geometries
SELECT id, name_en FROM admin_counties WHERE NOT ST_IsValid(geom);

-- Fix attempt (if needed)
UPDATE admin_counties SET geom = ST_MakeValid(geom) WHERE NOT ST_IsValid(geom);


Normalize to MULTIPOLYGON:

UPDATE admin_counties
SET geom = ST_Multi(geom)
WHERE GeometryType(geom) = 'POLYGON';

2.7 Generalisation Strategy (Beyond Ireland)

Keep admin_counties name, but allow loading any region’s boundaries; don’t hard-code county names.

Keep facility_type ENUM but allow extension migrations to add coastguard, mountain_rescue, etc.

All import scripts accept SRC_FILE and SRC_LAYER env vars to point to new datasets.

Don’t assume language or address formats; keep properties JSONB for uncaptured attributes.

2.8 Deliverables for Part 2

✅ Schema SQL: 001, 010, 020, 030, 040 (as defined)

✅ Import scripts: import_counties.sh, import_facilities.sh (or seed_facilities.sql)

✅ Verification SQL: verify_basics.sql, verify_spatial.sql, performance_explain.sql

✅ Docs: /docs/db_verification.md (paste query outputs + short notes)

Rubric mapping:

Database Design & Spatial Data: Multiple geometry types, correct SRIDs, indexes ✅

Spatial Queries: Proximity (radius + KNN), containment, buffering/intersection ✅

Optimization: Verified with EXPLAIN ANALYZE and spatial indexes ✅

2.9 Next (Preview of Part 3)

In Part 3 (Middle Tier – Django & REST API) you will:

Create Django models mapped to these tables (managed=False for imported ones, or migrations if owned).

Implement custom Managers for the spatial queries above.

Build REST endpoints (DRF + rest_framework_gis) returning GeoJSON for: nearest, within radius, within county, coverage buffers.

Add validation and robust error messages for query params.

Part 3 — Middle Tier: Django MVC & REST API (with GeoDjango + DRF)
Agent Role & Success Criteria

You are the backend lead. Build a clean, testable Django backend exposing a secure, documented REST API for spatial operations over PostGIS data designed in Part 2.

You must deliver:

Django project with apps: core, boundaries, services, frontend.

Models that map to existing PostGIS tables (managed=False) or first-party migrations if you prefer Django to own the schema (choose one path and stick to it).

DRF + drf-gis serializers that return GeoJSON.

ViewSets with CRUD for facilities and spatial query endpoints: nearest (KNN), within radius, within county, polygon search, coverage buffers.

Robust validation & error handling, pagination, filtering.

Auth: read for all, write for authenticated; CSRF enabled for session auth; token or cookie-based auth acceptable.

Tests: unit tests for serializers & queries; API tests for endpoints (happy + error paths).

Docs: browsable API (DRF), endpoint table in README, example curl.

Rubric mapping: MVC structure ✅, RESTful design ✅, validation & security ✅.

3.1 Project Setup & Dependencies

Requirements (add to requirements.txt):

Django>=5.0
psycopg2-binary>=2.9
djangorestframework>=3.15
djangorestframework-gis>=1.0
django-filter>=24.3
python-dotenv>=1.0


Settings (settings.py):

Enable GIS + DRF + filters.

INSTALLED_APPS = [
    # Django core
    'django.contrib.admin','django.contrib.auth','django.contrib.contenttypes',
    'django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles',
    'django.contrib.gis',
    # 3rd party
    'rest_framework','django_filters',
    # Project apps
    'core','boundaries','services','frontend',
]

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer',
                                 'rest_framework.renderers.BrowsableAPIRenderer'],
    'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser'],
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        # optionally add TokenAuthentication if enabled
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
}


Database (settings.py) – point to your es_locator DB, use env vars:

import os
from dotenv import load_dotenv; load_dotenv()
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DB_NAME','es_locator'),
        'USER': os.getenv('DB_USER','postgres'),
        'PASSWORD': os.getenv('DB_PASS','postgres'),
        'HOST': os.getenv('DB_HOST','localhost'),
        'PORT': os.getenv('DB_PORT','5432'),
    }
}


.env.example

DB_NAME=es_locator
DB_USER=postgres
DB_PASS=postgres
DB_HOST=localhost
DB_PORT=5432
DJANGO_SECRET_KEY=replace-me
DJANGO_DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

3.2 URL Topology

lbs/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from services.api import FacilityViewSet
from boundaries.api import CountyViewSet

router = DefaultRouter()
router.register(r'facilities', FacilityViewSet, basename='facility')
router.register(r'counties', CountyViewSet, basename='county')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('', include('frontend.urls')),  # map UI
]

3.3 Models (mapping to PostGIS tables)

Choose one approach:
A) Use the SQL schema from Part 2 and set managed=False to map Django to existing tables; or
B) Let Django own the schema (migrations) and keep fields identical to Part 2.
For fastest integration with Part 2, proceed with (A).

boundaries/models.py

from django.contrib.gis.db import models

class County(models.Model):
    id = models.IntegerField(primary_key=True)
    source_id = models.TextField(null=True, blank=True)
    name_en = models.TextField()
    name_local = models.TextField(null=True, blank=True)
    iso_code = models.TextField(null=True, blank=True)
    geom = models.MultiPolygonField(srid=4326)

    class Meta:
        db_table = 'admin_counties'
        managed = False
        verbose_name = 'County'
        verbose_name_plural = 'Counties'

    def __str__(self):
        return self.name_en


services/models.py

from django.contrib.gis.db import models

FACILITY_CHOICES = (
    ('hospital','Hospital'),
    ('fire_station','Fire Station'),
    ('police_station','Police Station'),
    ('ambulance_base','Ambulance Base'),
)

class EmergencyFacilityQuerySet(models.QuerySet):
    # ORM equivalents to the SQL queries
    def within_radius(self, point, meters: float):
        return self.filter(geom__distance_lte=(point, meters))

    def knn_nearest(self, point, limit=5):
        return self.order_by(models.functions.Distance('geom', point))[:limit]

class EmergencyFacility(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    type = models.CharField(max_length=32, choices=FACILITY_CHOICES)
    address = models.TextField(null=True, blank=True)
    phone = models.TextField(null=True, blank=True)
    website = models.TextField(null=True, blank=True)
    properties = models.JSONField(default=dict, blank=True)
    geom = models.PointField(srid=4326)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    objects = EmergencyFacilityQuerySet.as_manager()

    class Meta:
        db_table = 'emergency_facility'
        managed = False
        verbose_name = 'Emergency Facility'
        verbose_name_plural = 'Emergency Facilities'

    def __str__(self):
        return f"{self.name} ({self.type})"

3.4 Serializers (GeoJSON)

services/serializers.py

from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import EmergencyFacility

class FacilityGeoSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = EmergencyFacility
        geo_field = 'geom'
        fields = ('id','name','type','address','phone','website','properties','created_at','updated_at')


boundaries/serializers.py

from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import County

class CountyGeoSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = County
        geo_field = 'geom'
        fields = ('id','name_en','name_local','iso_code')

3.5 API Views (CRUD + Spatial Query Actions)

Validation helpers — services/validators.py

from rest_framework.exceptions import ValidationError

def parse_float(name, value, minv=None, maxv=None):
    try:
        x = float(value)
    except (TypeError, ValueError):
        raise ValidationError({name: "Must be a number."})
    if minv is not None and x < minv:
        raise ValidationError({name: f"Must be ≥ {minv}."})
    if maxv is not None and x > maxv:
        raise ValidationError({name: f"Must be ≤ {maxv}."})
    return x

def validate_lat_lon(lat, lon):
    return (parse_float('lat', lat, -90, 90), parse_float('lon', lon, -180, 180))

def parse_positive_meters(value, default=10000, maxv=200000):
    if value is None:
        return default
    return parse_float('radius_m', value, 1, maxv)


services/api.py

from django.contrib.gis.geos import Point, GEOSGeometry
from django.contrib.gis.db.models.functions import Distance
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import EmergencyFacility
from .serializers import FacilityGeoSerializer
from .validators import validate_lat_lon, parse_positive_meters
from boundaries.models import County

class FacilityViewSet(viewsets.ModelViewSet):
    """
    RESTful endpoints + spatial query actions for emergency facilities.
    """
    queryset = EmergencyFacility.objects.all()
    serializer_class = FacilityGeoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['type']  # ?type=hospital
    ordering_fields = ['name','updated_at']

    # ---- Spatial actions ----

    @action(detail=False, methods=['get'], url_path='within-radius')
    def within_radius(self, request):
        lat, lon = validate_lat_lon(request.query_params.get('lat'), request.query_params.get('lon'))
        radius_m = parse_positive_meters(request.query_params.get('radius_m'))
        p = Point(float(lon), float(lat), srid=4326)
        qs = (self.get_queryset()
              .filter(geom__distance_lte=(p, radius_m))
              .annotate(distance=Distance('geom', p))
              .order_by('distance'))
        page = self.paginate_queryset(qs)
        ser = self.get_serializer(page or qs, many=True)
        return self.get_paginated_response(ser.data) if page is not None else Response(ser.data)

    @action(detail=False, methods=['get'], url_path='nearest')
    def nearest(self, request):
        lat, lon = validate_lat_lon(request.query_params.get('lat'), request.query_params.get('lon'))
        limit = int(request.query_params.get('limit', 5))
        limit = max(1, min(limit, 50))
        p = Point(float(lon), float(lat), srid=4326)
        qs = self.get_queryset().annotate(distance=Distance('geom', p)).order_by('distance')[:limit]
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=False, methods=['get'], url_path='within-county')
    def within_county(self, request):
        # by id or name
        county_id = request.query_params.get('id')
        name = request.query_params.get('name')
        if county_id:
            try:
                county = County.objects.get(pk=int(county_id))
            except (County.DoesNotExist, ValueError):
                return Response({"detail":"County not found."}, status=404)
        elif name:
            county = County.objects.filter(name_en__iexact=name).first()
            if not county:
                return Response({"detail":"County not found."}, status=404)
        else:
            return Response({"detail":"Provide county id or name parameter."}, status=400)

        qs = self.get_queryset().filter(geom__within=county.geom)
        page = self.paginate_queryset(qs)
        ser = self.get_serializer(page or qs, many=True)
        return self.get_paginated_response(ser.data) if page is not None else Response(ser.data)

    @action(detail=False, methods=['post'], url_path='within-polygon')
    def within_polygon(self, request):
        # expects GeoJSON polygon in {"geometry":{...}} or {"geom": "...WKT..."}
        geom_json = request.data.get('geometry') or request.data.get('geom')
        if not geom_json:
            return Response({"detail":"Provide GeoJSON in 'geometry' or WKT in 'geom'."}, status=400)
        try:
            if isinstance(geom_json, str):
                poly = GEOSGeometry(geom_json, srid=4326)
            else:
                poly = GEOSGeometry(str(geom_json), srid=4326)
        except Exception:
            return Response({"detail":"Invalid geometry."}, status=400)
        if poly.geom_type not in ('Polygon','MultiPolygon'):
            return Response({"detail":"Geometry must be Polygon or MultiPolygon."}, status=400)

        qs = self.get_queryset().filter(geom__within=poly)
        page = self.paginate_queryset(qs)
        ser = self.get_serializer(page or qs, many=True)
        return self.get_paginated_response(ser.data) if page is not None else Response(ser.data)

    @action(detail=False, methods=['get'], url_path='coverage-buffers')
    def coverage_buffers(self, request):
        # NOTE: this returns points with distances; buffers are for visualization client-side
        lat, lon = validate_lat_lon(request.query_params.get('lat'), request.query_params.get('lon'))
        radius_m = parse_positive_meters(request.query_params.get('radius_m'), default=10000, maxv=100000)
        p = Point(float(lon), float(lat), srid=4326)
        qs = (self.get_queryset()
              .filter(geom__distance_lte=(p, radius_m))
              .annotate(distance=Distance('geom', p))
              .order_by('distance'))
        ser = self.get_serializer(qs, many=True)
        # Client can draw circles at radius_m; or you can add a second endpoint to stream server-side buffers as polygons.
        return Response({"radius_m": radius_m, "results": ser.data})


boundaries/api.py

from rest_framework import viewsets
from .models import County
from .serializers import CountyGeoSerializer

class CountyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = County.objects.all().order_by('name_en')
    serializer_class = CountyGeoSerializer
    filterset_fields = ['iso_code','name_en']

3.6 CRUD (Create/Update/Delete) on Facilities

Even when mapping to an existing table, allow authenticated writes:

Permissions: DjangoModelPermissionsOrAnonReadOnly → grant add_change_delete via Django admin to your test user.

CSRF: enabled by default for session-auth; for API tools, use token auth if preferred.

Validation: rely on DRF serializer + custom checks if needed.

Create example (GeoJSON Feature payload):

{
  "type": "Feature",
  "geometry": {"type":"Point","coordinates":[-6.26,53.35]},
  "properties": {
    "name": "Sample Hospital",
    "type": "hospital",
    "address": "Dublin",
    "phone": "+353-1-0000000",
    "website": "https://example.org",
    "properties": {"aed":"yes","beds":450}
  }
}

3.7 API Endpoints (Summary)
Endpoint	Method	Params / Body	Purpose
/api/facilities/	GET	?type=hospital&limit=&offset=	List facilities (GeoJSON)
/api/facilities/{id}/	GET	—	Detail (GeoJSON)
/api/facilities/	POST	GeoJSON Feature	Create (auth required)
/api/facilities/{id}/	PATCH/PUT	GeoJSON Feature	Update (auth required)
/api/facilities/{id}/	DELETE	—	Delete (auth required)
/api/facilities/within-radius	GET	lat,lon,radius_m	Proximity search
/api/facilities/nearest	GET	lat,lon,limit	KNN nearest
/api/facilities/within-county	GET	id or name	Containment by county
/api/facilities/within-polygon	POST	GeoJSON Polygon	Containment by polygon
/api/facilities/coverage-buffers	GET	lat,lon,radius_m	For drawing coverage circles client-side
/api/counties/	GET	?name_en=	County polygons (GeoJSON)
/api/counties/{id}/	GET	—	County details

Error responses: always JSON, e.g.

{"detail":"Provide county id or name parameter."}

3.8 Security & Hardening

Use allowlist CORS only if you split frontend; otherwise keep same-origin.

Validate all inputs; clamp limits: limit ≤ 50, radius_m ≤ 200000.

Use database SRID guards (already in Part 2).

For production/Docker mode:

DEBUG=False, set ALLOWED_HOSTS, secure cookies, HSTS (via Nginx), SECURE_PROXY_SSL_HEADER.

Add simple throttling if needed (DRF throttling classes) for public endpoints.

3.9 Tests (must pass)

services/tests/test_api.py

Seed small fixture (from Part 2).

List: /api/facilities/?type=hospital returns 200 + GeoJSON features.

Nearest: /api/facilities/nearest?lat=53.3498&lon=-6.2603&limit=3 returns 200, length 3, ordered by distance.

Within radius: returns only features within meters threshold.

Within county: returns features contained; 400/404 on bad params.

Create/Update/Delete: unauthorized → 403; authorized → 201/200/204.

boundaries/tests/test_api.py

/api/counties/ returns features; geometry present.

Run tests:

python manage.py test services boundaries

3.10 Developer Experience Enhancements (nice-to-have)

Browsable API enabled (already in REST_FRAMEWORK).

OpenAPI schema: add drf-spectacular (optional) to auto-generate /api/schema/ + Swagger UI.

Caching: Cache county list (locmem) and common radius searches (keyed by lat/lon/radius/type) to speed up demos.

Admin: register EmergencyFacility and County with LeafletGeoAdmin for manual edits and quick inspection.

3.11 Deliverables for Part 3

✅ Django apps & settings configured for GeoDjango + DRF

✅ Models (managed=False mapping) for admin_counties, emergency_facility

✅ GeoJSON serializers

✅ ViewSets with CRUD + spatial actions (nearest, within-radius, within-county, within-polygon, coverage)

✅ Validation & errors

✅ Tests (unit + API)

✅ Endpoint documentation (README table + example curl)

Rubric alignment:

MVC & API Design: clean app separation, RESTful endpoints, good organization ✅

Data Handling & Validation: strict param validation, secure permissions, clear errors, GeoJSON serialization ✅

3.12 Next (Preview of Part 4 – Front-End & Map UI)

In Part 4, you will build a responsive Leaflet + Bootstrap UI:

Single-page map with filters (type, radius), “Locate me”, draw polygon (Leaflet.draw).

Calls to the endpoints above; renders GeoJSON layers and popups.

Accessibility basics (ARIA, keyboard focus, contrast) to push UI marks toward “Excellent.”

Agent Role & Success Criteria

You are the front-end lead. Deliver a responsive, accessible, and fast map UI that consumes the REST API from Part 3.

You must deliver:

A single-page map UI built with Bootstrap 5 + Leaflet (and optional MarkerCluster + Leaflet.draw).

Filters (service type, radius), “Locate me”, Nearest and Within radius queries, Within county selector, Draw polygon search.

Polished popups, mobile-first layout, keyboard and screen-reader support (WCAG 2.1 AA intent).

Graceful error states and loading indicators.

Simple smoke tests and screenshots for the README.

Rubric mapping:

Responsive Design ✅

Mapping Integration (interactive, custom styling, smooth performance) ✅

4.1 Front-End App Structure

Create the following within your Django project:

/frontend
  /templates/frontend
    base.html
    map.html
  /static/frontend
    css/map.css
    js/map.js
    js/icons.js
    js/api.js


URLs & View

frontend/urls.py

from django.urls import path
from .views import MapView

urlpatterns = [ path('', MapView.as_view(), name='home') ]


frontend/views.py

from django.views.generic import TemplateView
class MapView(TemplateView):
    template_name = 'frontend/map.html'


Wire into project URLs (already in Part 3): path('', include('frontend.urls')).

4.2 Base Template & Vendor Assets

Use Bootstrap 5 + Leaflet (and optional plugins via CDN for speed in dev).

frontend/templates/frontend/base.html

<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Emergency Services Locator</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <!-- Bootstrap 5 -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" />
  <!-- Leaflet -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <!-- MarkerCluster (optional) -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"/>
  <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"/>
  <!-- Leaflet.draw (optional) -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css"/>
  <link rel="stylesheet" href="{% static 'frontend/css/map.css' %}">
</head>
<body class="bg-light">
  <a class="visually-hidden-focusable" href="#map" id="skipmap">Skip to map</a>
  {% block content %}{% endblock %}
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
  <script src="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js"></script>
  <script src="{% static 'frontend/js/api.js' %}"></script>
  <script src="{% static 'frontend/js/icons.js' %}"></script>
  <script src="{% static 'frontend/js/map.js' %}"></script>
</body>
</html>

4.3 Map Page Layout (Responsive, Accessible)

frontend/templates/frontend/map.html

{% extends 'frontend/base.html' %}
{% block content %}
<main class="container-fluid py-3">
  <div class="row g-3">
    <!-- Controls -->
    <aside class="col-12 col-lg-3">
      <div class="card shadow-sm">
        <div class="card-body">
          <h1 class="h4 mb-3">Emergency Services Locator</h1>

          <form id="filters" class="vstack gap-3" aria-describedby="filterHelp">
            <div>
              <label for="type" class="form-label">Service type</label>
              <select id="type" class="form-select" aria-label="Service type">
                <option value="">All</option>
                <option value="hospital">Hospital</option>
                <option value="fire_station">Fire Station</option>
                <option value="police_station">Garda / Police</option>
                <option value="ambulance_base">Ambulance Base</option>
              </select>
            </div>

            <div>
              <label for="radius" class="form-label">Radius (km)</label>
              <input type="range" id="radius" class="form-range" min="1" max="50" value="10" />
              <div class="d-flex justify-content-between">
                <span class="text-muted">1</span>
                <span><output id="radiusOut" for="radius">10</output> km</span>
                <span class="text-muted">50</span>
              </div>
            </div>

            <div class="btn-group" role="group" aria-label="Actions">
              <button id="locateBtn" type="button" class="btn btn-primary">Locate me</button>
              <button id="nearestBtn" type="button" class="btn btn-outline-primary">Nearest</button>
              <button id="radiusBtn" type="button" class="btn btn-outline-secondary">Within radius</button>
            </div>

            <hr/>

            <div>
              <label for="countySelect" class="form-label">Filter by county</label>
              <select id="countySelect" class="form-select">
                <option value="">— Choose county —</option>
              </select>
            </div>

            <div class="form-text" id="filterHelp">
              Use the tools above or draw a polygon on the map to filter facilities.
            </div>
          </form>

          <div class="mt-3 small text-muted" aria-live="polite" id="statusMsg">Ready.</div>
        </div>
      </div>
    </aside>

    <!-- Map -->
    <section class="col-12 col-lg-9">
      <div id="map" class="rounded shadow-sm" role="application" aria-label="Emergency services map" tabindex="0"></div>
    </section>
  </div>
</main>
{% endblock %}


frontend/static/frontend/css/map.css

#map { height: calc(100vh - 8rem); min-height: 480px; }
.leaflet-container:focus { outline: 3px solid #0d6efd; }
.marker-hospital { filter: saturate(1.2); }
.marker-fire_station { }
.marker-police_station { }
.marker-ambulance_base { }

4.4 API Client (Fetch helpers)

frontend/static/frontend/js/api.js

const API = {
  async counties() {
    const res = await fetch('/api/counties/?limit=200');
    if (!res.ok) throw new Error('Failed to load counties');
    return res.json();
  },
  async facilitiesList(params = {}) {
    const url = new URL('/api/facilities/', location.origin);
    Object.entries(params).forEach(([k,v]) => (v!==undefined && v!=='') && url.searchParams.set(k,v));
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load facilities');
    return res.json();
  },
  async withinRadius({lat, lon, radius_m, type}) {
    const url = new URL('/api/facilities/within-radius/', location.origin);
    url.searchParams.set('lat', lat); url.searchParams.set('lon', lon);
    url.searchParams.set('radius_m', radius_m);
    if (type) url.searchParams.set('type', type);
    const res = await fetch(url);
    if (!res.ok) throw new Error('Radius query failed');
    return res.json();
  },
  async nearest({lat, lon, limit=5, type}) {
    const url = new URL('/api/facilities/nearest/', location.origin);
    url.searchParams.set('lat', lat); url.searchParams.set('lon', lon);
    url.searchParams.set('limit', limit);
    if (type) url.searchParams.set('type', type);
    const res = await fetch(url);
    if (!res.ok) throw new Error('Nearest query failed');
    return res.json();
  },
  async withinCounty({id, name, type}) {
    const url = new URL('/api/facilities/within-county/', location.origin);
    if (id) url.searchParams.set('id', id);
    if (name) url.searchParams.set('name', name);
    if (type) url.searchParams.set('type', type);
    const res = await fetch(url);
    if (!res.ok) throw new Error('County query failed');
    return res.json();
  },
  async withinPolygon(geojson, type) {
    const res = await fetch('/api/facilities/within-polygon/', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({geometry: geojson.geometry, type})
    });
    if (!res.ok) throw new Error('Polygon query failed');
    return res.json();
  }
};
export default API;

4.5 Marker Icons (per facility type)

frontend/static/frontend/js/icons.js

export const icons = {
  hospital: L.icon({ iconUrl:'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png', iconSize:[25,41], iconAnchor:[12,41], className:'marker-hospital' }),
  fire_station: L.icon({ iconUrl:'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png', iconSize:[25,41], iconAnchor:[12,41], className:'marker-fire_station' }),
  police_station: L.icon({ iconUrl:'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png', iconSize:[25,41], iconAnchor:[12,41], className:'marker-police_station' }),
  ambulance_base: L.icon({ iconUrl:'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png', iconSize:[25,41], iconAnchor:[12,41], className:'marker-ambulance_base' }),
  default: L.icon({ iconUrl:'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png', iconSize:[25,41], iconAnchor:[12,41] })
};


(You can later swap to custom SVGs.)

4.6 Map Logic & Interactions

frontend/static/frontend/js/map.js

import API from './api.js';
import { icons } from './icons.js';

const state = {
  map: null,
  cluster: null,
  countyLayer: null,
  drawn: null,
  userLatLng: null
};

const $ = (sel) => document.querySelector(sel);
const status = (msg) => { $('#statusMsg').textContent = msg; };
const kmToM = (km) => Math.round(Number(km) * 1000);

function popupHtml(f) {
  const p = f.properties || f;
  const meta = p.properties || {};
  const phone = p.phone ? `<div>☎ ${p.phone}</div>` : '';
  const web = p.website ? `<div>🔗 <a href="${p.website}" target="_blank" rel="noopener">Website</a></div>` : '';
  return `
    <div class="fw-semibold">${p.name}</div>
    <div class="text-muted small mb-1">${p.type.replace('_',' ')}</div>
    <div class="small">${p.address || ''}</div>
    ${phone}${web}
    ${meta.ae ? `<div class="badge bg-success mt-1">A&E</div>`:''}
  `;
}

function featureToMarker(feature, latlng) {
  const t = feature.properties?.type || 'default';
  return L.marker(latlng, { icon: icons[t] || icons.default }).bindPopup(popupHtml(feature));
}

async function loadCounties() {
  try {
    const data = await API.counties(); // GeoJSON-like
    const select = $('#countySelect');
    data.features.forEach(feat => {
      const opt = document.createElement('option');
      opt.value = feat.id || feat.properties.id || feat.properties?.pk || ''; // accommodate drf-gis id
      opt.textContent = feat.properties?.name_en || `County ${opt.value}`;
      select.appendChild(opt);
    });

    // Optional: draw county boundaries (light)
    state.countyLayer = L.geoJSON(data, {
      style: { color:'#6c757d', weight:1, fill:false, interactive:false }
    }).addTo(state.map);
  } catch (e) {
    console.error(e);
    status('Failed to load counties.');
  }
}

function clearMarkers() {
  if (state.cluster) {
    state.map.removeLayer(state.cluster);
  }
  state.cluster = L.markerClusterGroup({ chunkedLoading:true });
  state.map.addLayer(state.cluster);
}

function renderFacilities(geojson, { fit=false } = {}) {
  clearMarkers();
  const layer = L.geoJSON(geojson, {
    pointToLayer: featureToMarker
  });
  state.cluster.addLayer(layer);
  if (fit && layer.getLayers().length) {
    state.map.fitBounds(layer.getBounds(), { padding:[20,20] });
  }
}

async function queryNearest() {
  const type = $('#type').value || undefined;
  if (!state.userLatLng) {
    await locateUser(true);
  }
  const {lat, lng} = state.userLatLng;
  status('Finding nearest…');
  const data = await API.nearest({lat, lon: lng, limit:5, type});
  renderFacilities(data, { fit:true });
  status(`Found ${data.features?.length ?? data.length ?? 0} nearest facilities.`);
}

async function queryWithinRadius() {
  const type = $('#type').value || undefined;
  if (!state.userLatLng) {
    await locateUser(true);
  }
  const {lat, lng} = state.userLatLng;
  const radius_km = $('#radius').value;
  status(`Searching within ${radius_km} km…`);
  const data = await API.withinRadius({lat, lon: lng, radius_m: kmToM(radius_km), type});
  renderFacilities(data, { fit:true });
  L.circle(state.userLatLng, { radius: kmToM(radius_km), color:'#0d6efd', weight:1 }).addTo(state.map);
  status(`Showing results within ${radius_km} km.`);
}

async function queryWithinCounty() {
  const id = $('#countySelect').value;
  const type = $('#type').value || undefined;
  if (!id) return;
  status('Filtering by county…');
  const data = await API.withinCounty({id, type});
  renderFacilities(data, { fit:true });
  status('Showing facilities within county.');
}

async function locateUser(fly=false) {
  status('Locating…');
  return new Promise((resolve, reject) => {
    state.map.locate({ setView: false, maxZoom: 12, enableHighAccuracy: true })
      .on('locationfound', (e) => {
        state.userLatLng = e.latlng;
        L.marker(e.latlng, { title:'Your location'}).addTo(state.map);
        if (fly) state.map.flyTo(e.latlng, 12);
        status('Location set.');
        resolve(e.latlng);
      })
      .on('locationerror', () => { status('Unable to get location. You can still use county/polygon.'); resolve(null); });
  });
}

function setupDraw() {
  const drawnItems = new L.FeatureGroup().addTo(state.map);
  const drawCtrl = new L.Control.Draw({
    draw: { marker:false, rectangle:true, polygon:true, circle:false, polyline:false, circlemarker:false },
    edit: { featureGroup: drawnItems }
  });
  state.map.addControl(drawCtrl);

  state.map.on(L.Draw.Event.CREATED, async (e) => {
    drawnItems.clearLayers();
    const lyr = e.layer; drawnItems.addLayer(lyr);
    const gj = lyr.toGeoJSON();
    status('Polygon drawn — querying…');
    const type = $('#type').value || undefined;
    const data = await API.withinPolygon(gj, type);
    renderFacilities(data, { fit:true });
    status('Results filtered by drawn area.');
  });
}

function setupEvents() {
  $('#radius').addEventListener('input', e => $('#radiusOut').value = e.target.value);
  $('#locateBtn').addEventListener('click', locateUser);
  $('#nearestBtn').addEventListener('click', () => queryNearest().catch(err => { console.error(err); status('Nearest query failed.'); }));
  $('#radiusBtn').addEventListener('click', () => queryWithinRadius().catch(err => { console.error(err); status('Radius query failed.'); }));
  $('#countySelect').addEventListener('change', () => queryWithinCounty().catch(err => { console.error(err); status('County query failed.'); }));
  $('#type').addEventListener('change', () => {
    // Re-run last query context if we want; for simplicity, do nothing until user triggers an action.
  });
}

function initMap() {
  state.map = L.map('map', { zoomControl: true }).setView([53.3498, -6.2603], 7); // Ireland default
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19, attribution: '&copy; OpenStreetMap'
  }).addTo(state.map);
  clearMarkers();
  setupDraw();
  setupEvents();
  loadCounties();
  status('Map ready. Choose a filter or click “Locate me”.');
}

// Boot
document.addEventListener('DOMContentLoaded', initMap);

4.7 Accessibility & UX Requirements (WCAG 2.1 AA intent)

Keyboard support:

role="application" on map + focus outline in CSS.

Ensure controls are reachable with Tab order (toolbar before map).

Screen reader hints:

aria-live="polite" status region updates query progress (see #statusMsg).

Labels on all form controls; avoid icon-only buttons.

Contrast & spacing: Bootstrap defaults are acceptable; ensure 4.5:1 text contrast.

Touch targets: buttons ≥ 44×44 px (Bootstrap meets this).

Skip link to map provided at top of page.

Motion: avoid excessive fly animations; only on locate event.

4.8 Performance Tuning

MarkerCluster to handle 100s–1k points smoothly.

Use chunkedLoading and defer polygon (county) rendering.

For large responses, paginate (DRF already paginates) and fitBounds to current page.

Debounce rapid control changes if you add real-time filtering.

4.9 Error Handling & Empty States

Status text explains when a query fails (network/API error).

If the result set is empty, show a Bootstrap toast or set status('No facilities found for this query.').

On geolocation denied, keep county/polygon queries fully usable.

4.10 Manual QA Checklist (Screenshots for README)

Capture screenshots to include under “Screenshots”:

Default Ireland view with sidebar.

Locate me + within radius (10 km) with circle visible.

Nearest results with clustered markers and open popup.

Within county (e.g., Dublin) filtered.

Drawn polygon filter in action.

Mobile viewport (iPhone width) with stacked layout.

4.11 Optional Enhancements (Nice to have)

Legend / Layer control toggling facility types.

Heatmap layer (client-side) if you add many POIs.

Shareable URLs (encode last query in querystring and restore on load).

Offline tiles for demos without internet (serve tiles locally if needed).

Internationalisation (strings via Django i18n).

4.12 Deliverables for Part 4

✅ map.html, base.html (Bootstrap + Leaflet).

✅ map.css, api.js, icons.js, map.js (working controls).

✅ Accessible controls, status region, keyboard focus on map.

✅ MarkerCluster, Draw polygon, Within radius circle.

✅ Screenshots added to README.

Rubric alignment:

Responsive Design: clean Bootstrap layout, mobile-friendly, intuitive UX.

Mapping Integration: Leaflet interactivity (geolocate, radius, polygon, county, popups), smooth performance.

Part 5 — Deployment & Ops (Local + Docker Bonus)
Agent Role & Success Criteria

You are the DevOps lead. Ship the Emergency Services Locator so it runs reliably on any assessor’s laptop with one or two commands.

You must deliver:

✅ Local (non-Docker) run path using venv and .env.

✅ Docker Compose stack with a custom subnet, separate images for Django (gunicorn), PostGIS, PgAdmin, Nginx reverse proxy, named volumes, and healthchecks.

✅ Environment-based config (dev vs “prod-like”).

✅ Security headers via Nginx, secrets via env, and no secrets in Git.

✅ Clear README sections with copy-paste commands.

✅ Troubleshooting notes and health verification.

Rubric mapping:

Implementation: complete setup, proper networking, volumes, production-style config.

Deployment: accessible, stable, security considerations applied.

Bonus: custom network, split images, reverse proxy, env-based config, security headers.

5.1 Files & Structure

Add at repo root:

.env.example
Makefile                      (optional, convenience)
docker-compose.yml
docker/                       (build context)
  web/Dockerfile
  web/gunicorn.conf.py
  nginx/Dockerfile
  nginx/nginx.conf
docs/
  deployment.md
  architecture.png


Keep your existing /db (schema/import/queries), /frontend, /services, /boundaries, etc.

5.2 Environment Variables

.env.example

# Django
DJANGO_SECRET_KEY=replace-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

# Database
DB_NAME=es_locator
DB_USER=postgres
DB_PASS=postgres
DB_HOST=localhost
DB_PORT=5432

# Docker overrides (compose will inject these)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=es_locator

# PgAdmin (for Docker)
PGADMIN_DEFAULT_EMAIL=admin@example.com
PGADMIN_DEFAULT_PASSWORD=admin123

# Gunicorn
WORKERS=3
TIMEOUT=60


Rules for the AI:

Never commit a real DJANGO_SECRET_KEY.

settings.py must read from env and toggle DEBUG/ALLOWED_HOSTS/SECURE_* flags by environment (see §5.6).

5.3 Local (non-Docker) Runbook

Add a README section with these exact steps (AI must test them):

# 1) Python env
python -m venv .venv
source .venv/bin/activate   # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt

# 2) Env
cp .env.example .env
# Edit .env if needed (DB creds)

# 3) Postgres + PostGIS must be running locally.
# Create DB & enable extensions, or run our bootstrap SQL:
createdb es_locator
psql -d es_locator -c "CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS pg_trgm;"

# 4) Apply schema + import minimal seed
psql -d es_locator -f db/schema/001_extensions.sql
psql -d es_locator -f db/schema/010_bounds_counties.sql
psql -d es_locator -f db/schema/020_services_facilities.sql
psql -d es_locator -f db/schema/040_constraints_indexes.sql
psql -d es_locator -f db/import/seed_facilities.sql   # quick demo data

# 5) Django setup
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py createsuperuser  # provide test creds per README

# 6) Run dev server
python manage.py runserver
# Visit http://127.0.0.1:8000/


Test credentials (example to include in README):

username: demo

password: DemoPass123!

admin at /admin/

5.4 Docker Compose (Bonus Path, Recommended)
5.4.1 Custom Network & Volumes

Use a custom subnet for the stack (bonus requirement).

Named volumes for DB storage and static files.

docker-compose.yml

version: "3.9"

networks:
  esnet:
    ipam:
      driver: default
      config:
        - subnet: 172.28.0.0/16

volumes:
  pgdata:
  staticfiles:

services:
  db:
    image: postgis/postgis:16-3.4
    container_name: es_db
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      POSTGRES_DB: ${POSTGRES_DB:-es_locator}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 10
    networks: [esnet]

  web:
    build:
      context: ./docker/web
      dockerfile: Dockerfile
    container_name: es_web
    depends_on:
      db:
        condition: service_healthy
    env_file: .env
    environment:
      DJANGO_DEBUG: "False"
      DB_HOST: db
      DB_PORT: 5432
      DJANGO_ALLOWED_HOSTS: "localhost,127.0.0.1"
      WORKERS: ${WORKERS:-3}
      TIMEOUT: ${TIMEOUT:-60}
    command: ["/bin/sh","-c","/app/entrypoint.sh"]
    volumes:
      - staticfiles:/app/staticfiles
      - ./:/workspace:ro  # optional: mount source read-only for reference
    networks: [esnet]

  nginx:
    build:
      context: ./docker/nginx
      dockerfile: Dockerfile
    container_name: es_nginx
    depends_on:
      - web
    ports:
      - "80:80"
    volumes:
      - staticfiles:/staticfiles:ro
    networks: [esnet]

  pgadmin:
    image: dpage/pgadmin4:8
    container_name: es_pgadmin
    depends_on:
      - db
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_DEFAULT_EMAIL:-admin@example.com}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_DEFAULT_PASSWORD:-admin123}
    ports:
      - "5050:80"
    networks: [esnet]

5.4.2 Web (Django + gunicorn) Image

docker/web/Dockerfile

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    binutils libproj-dev gdal-bin postgresql-client \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app

# Gunicorn config + entry
COPY docker/web/gunicorn.conf.py /app/gunicorn.conf.py
RUN chmod +x /app/docker/web/entrypoint.sh

EXPOSE 8000
CMD ["bash","-lc","/app/docker/web/entrypoint.sh"]


docker/web/gunicorn.conf.py

import multiprocessing, os
bind = "0.0.0.0:8000"
workers = int(os.getenv("WORKERS", multiprocessing.cpu_count() * 2 + 1))
timeout = int(os.getenv("TIMEOUT", "60"))
accesslog = "-"
errorlog = "-"


docker/web/entrypoint.sh

#!/usr/bin/env bash
set -euo pipefail

python manage.py collectstatic --noinput
python manage.py migrate --noinput || true

# Load minimal seed if table empty (idempotent safety)
psql "host=${DB_HOST} port=${DB_PORT} dbname=${DB_NAME} user=${DB_USER} password=${DB_PASS}" \
  -c "SELECT 1 FROM emergency_facility LIMIT 1" >/dev/null 2>&1 || true
psql "host=${DB_HOST} port=${DB_PORT} dbname=${DB_NAME} user=${DB_USER} password=${DB_PASS}" \
  -f db/import/seed_facilities.sql || true

exec gunicorn lbs.wsgi:application -c /app/gunicorn.conf.py


Adjust project module name lbs if yours differs.

5.4.3 Nginx Reverse Proxy

docker/nginx/Dockerfile

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/nginx.conf


docker/nginx/nginx.conf

worker_processes auto;
events { worker_connections 1024; }
http {
  include       mime.types;
  sendfile      on;
  tcp_nopush    on;
  tcp_nodelay   on;
  server_tokens off;

  # Basic security headers
  map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
  }

  server {
    listen 80;
    server_name _;

    # Security headers (prod-like)
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header Referrer-Policy no-referrer-when-downgrade;
    add_header X-XSS-Protection "1; mode=block";
    # HSTS only when TLS is used (not in this local HTTP example)
    # add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

    # Static files served by Nginx
    location /static/ {
      alias /staticfiles/;
      access_log off;
      expires 7d;
    }

    # Proxy to Django
    location / {
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_pass http://es_web:8000;
      proxy_read_timeout 120s;
    }
  }
}

5.5 Compose Commands (README Snippets)
# Build & run
cp .env.example .env
docker compose up --build

# App: http://localhost/
# Admin: http://localhost/admin/
# PgAdmin: http://localhost:5050/  (add server: host=db, user/pass from .env)

# Tear down (preserve DB volume)
docker compose down

# Full reset (drops DB volume)
docker compose down -v


Optional Makefile for convenience:

up:
\tdocker compose up --build
down:
\tdocker compose down
reset:
\tdocker compose down -v

5.6 Production-Style Settings (Env-gated)

In settings.py:

import os
DEBUG = os.getenv("DJANGO_DEBUG","True") == "True"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY","change-me")
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS","127.0.0.1,localhost").split(",")

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # when behind TLS proxy
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG


Local dev: DEBUG=True, relaxed hosts.

Compose “prod-like”: set DJANGO_DEBUG=False, keep hosts restricted.

No hardcoded secrets.

5.7 Post-Deploy Health Checks

Include a short deployment checklist in docs/deployment.md:

 /api/facilities/?limit=1 → 200 with GeoJSON

 /api/facilities/nearest?lat=53.3498&lon=-6.2603&limit=3 → 200, 1–3 features

 /api/counties/ → 200, features present

 Frontend map loads tiles and controls respond

 Admin accessible; login works with test user

 Nginx logs show 200s; docker ps healthchecks all healthy

5.8 Security Considerations (explicitly call out in README)

Secrets only via env; no secrets committed.

Nginx supplies baseline headers; HSTS only with TLS.

DRF permissions: anonymous read; writes require authenticated user with model perms.

Request validation (lat/lon/radius/limit), clamped ranges.

Optional DRF throttling on public endpoints (basic rate limit).

5.9 Troubleshooting

Ports busy: change 5432/80/5050 in compose or stop local services.

DB migrations fail at first boot: container might race; compose uses depends_on: healthy. Re-run docker compose up.

Static files missing: ensure collectstatic runs; check staticfiles volume is mounted to Nginx.

CORS: not needed in single-origin setup; if splitting front/back, enable django-cors-headers for dev only.

SRID errors: confirm imports reprojected to EPSG:4326 (§2.4 scripts).

5.10 Deliverables for Part 5

✅ .env.example and env-based settings.py toggles

✅ docker-compose.yml with custom subnet and separate images (web, db, pgadmin, nginx)

✅ docker/web (Dockerfile, gunicorn config, entrypoint)

✅ docker/nginx (Dockerfile, nginx.conf with security headers)

✅ README deployment sections (local + Docker), with copy-paste commands

✅ docs/deployment.md checklist + screenshots

Rubric alignment:

Implementation: complete, services work, volumes & network, production-like.

Deployment: accessible at http://localhost/, stable under reverse proxy, security headers noted.

Bonus (+5): custom subnet, separate images, Nginx reverse proxy, env-based config & security.