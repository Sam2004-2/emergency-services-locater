#!/usr/bin/env bash
set -euo pipefail

: "${DB_HOST:=localhost}"
: "${DB_PORT:=5432}"
: "${DB_NAME:=es_locator}"
: "${DB_USER:=postgres}"
: "${DB_PASS:=postgres}"
: "${SRC_FILE:=./spatial_data/facilities/ireland_emergency_facilities.geojson}"

export PGPASSWORD="$DB_PASS"

ogr2ogr -f "PostgreSQL" \
  PG:"host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=$DB_USER password=$DB_PASS" \
  "$SRC_FILE" \
  -nln _tmp_facilities \
  -overwrite \
  -lco GEOMETRY_NAME=geom \
  -nlt POINT \
  -t_srs EPSG:4326

psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<'SQL'
INSERT INTO emergency_facility (name, type, address, phone, website, properties, geom)
SELECT
  COALESCE(name, 'Unnamed'),
  CASE
    WHEN LOWER(category) LIKE '%hospital%' THEN 'hospital'::facility_type
    WHEN LOWER(category) LIKE '%fire%' THEN 'fire_station'::facility_type
    WHEN LOWER(category) LIKE '%police%' OR LOWER(category) LIKE '%garda%' THEN 'police_station'::facility_type
    WHEN LOWER(category) LIKE '%ambulance%' THEN 'ambulance_base'::facility_type
    ELSE 'hospital'::facility_type
  END,
  address,
  phone,
  website,
  to_jsonb(row_to_json(t)) - 'geom',
  geom
FROM _tmp_facilities t;
DROP TABLE IF EXISTS _tmp_facilities;
SQL
