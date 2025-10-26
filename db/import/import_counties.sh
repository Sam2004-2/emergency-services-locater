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
