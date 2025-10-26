# Data Import Guide

This guide explains how to import real-world data for counties and emergency services from open data APIs.

## Overview

The system provides Django management commands to automatically fetch and import:
- **County Boundaries**: Irish administrative boundaries from OpenStreetMap
- **Emergency Facilities**: Hospitals, fire stations, police stations, and ambulance bases from multiple sources

## Prerequisites

Install the updated requirements:
```bash
pip install -r requirements.txt
```

Or in Docker:
```bash
docker compose up --build
```

## Importing Counties

### Quick Start (OpenStreetMap)

Import all 26 Irish counties from OpenStreetMap:

```bash
python manage.py import_counties
```

Or in Docker:
```bash
docker exec es_web python manage.py import_counties
```

### Options

```bash
# Clear existing counties before importing
python manage.py import_counties --clear

# Import from custom GeoJSON URL
python manage.py import_counties --source=geojson --url="https://example.com/counties.geojson"
```

### What It Does

- Fetches county boundaries from OpenStreetMap Nominatim API
- Imports all 26 Irish counties with proper geometries
- Includes Irish language names (Gaeilge)
- Adds ISO codes for each county
- Rate-limited to be respectful to OSM servers (~1.5 seconds per county)

**Expected time**: ~40-60 seconds for all 26 counties

## Importing Emergency Facilities

### Quick Start (Ireland)

Import emergency services for Ireland from OpenStreetMap:

```bash
# Import all facility types
python manage.py import_facilities

# Import specific types only
python manage.py import_facilities --types=hospital,fire_station

# Import for specific region using bounding box (Ireland)
python manage.py import_facilities --bbox=-10.5,51.4,-5.4,55.4
```

Or in Docker:
```bash
docker exec es_web python manage.py import_facilities
```

### Options

```bash
# Clear existing facilities before importing
python manage.py import_facilities --clear

# Import limited number per type (useful for testing)
python manage.py import_facilities --types=hospital --limit=10

# Import from custom GeoJSON
python manage.py import_facilities --source=geojson --url="https://example.com/facilities.geojson"

# Import for different country
python manage.py import_facilities --country="United Kingdom" --types=hospital
```

### Facility Types

- `hospital` - Hospitals and medical centers
- `fire_station` - Fire stations and fire brigades
- `police_station` - Police stations and Garda stations
- `ambulance_base` - Ambulance stations and depots

### Data Sources

#### 1. OpenStreetMap (Default - Recommended)
- **Coverage**: Global
- **Quality**: High, community-maintained
- **API**: Overpass API
- **Rate Limit**: 5 seconds between requests (to avoid 429/504 errors)
- **Query Timeout**: 90 seconds per facility type
- **Request Timeout**: 120 seconds
- **Typical Results**: 
  - 100-150 hospitals in Ireland
  - 50-80 fire stations
  - 50-100 police stations
  - 20-40 ambulance bases

#### 2. Custom GeoJSON
- Import from any GeoJSON URL
- Useful for custom datasets or government open data portals

### Expected Import Times

- **Quick test** (10 facilities per type): ~15-20 seconds
- **Single facility type** (e.g., all hospitals): ~2-3 minutes
- **Full Ireland import** (all 4 types): ~10-15 minutes (with 5-second delays)
- **Large country** (e.g., UK): ~30-60 minutes

## Complete Setup Example

Fresh installation with real data:

```bash
# 1. Set up database
docker compose up -d

# 2. Import counties
docker exec es_web python manage.py import_counties

# 3. Import emergency facilities
docker exec es_web python manage.py import_facilities

# 4. Create admin user
docker exec es_web python manage.py createsuperuser

# 5. Access the application
open http://localhost/
```

## Data Quality Notes

### OpenStreetMap Data
- **Pros**: Comprehensive, global coverage, regularly updated, free
- **Cons**: Quality varies by region, some facilities may lack complete info
- **Coverage**: Excellent for Ireland, UK, US, Western Europe

### Improving Data Quality

The imported data is only as good as the source. You can:

1. **Contribute to OpenStreetMap**: Update missing/incorrect facilities at [openstreetmap.org](https://www.openstreetmap.org)
2. **Manual corrections**: Use Django admin to fix individual facilities
3. **Custom imports**: Use `--source=geojson` with curated datasets

## Automation

### Update Data Periodically

Add to cron or task scheduler:

```bash
# Update counties monthly
0 0 1 * * docker exec es_web python manage.py import_counties --clear

# Update facilities weekly
0 2 * * 0 docker exec es_web python manage.py import_facilities --clear
```

### Django Admin Integration

You can also trigger imports from Django admin by creating custom admin actions (see `services/admin.py` and `boundaries/admin.py`).

## Troubleshooting

### Import Fails or Times Out

**Problem**: Overpass API timeout or rate limiting (429 Too Many Requests, 504 Gateway Timeout)

**Solutions**:
```bash
# The import command now includes 5-second delays between requests
# But if you still encounter issues:

# Use smaller bounding box
python manage.py import_facilities --bbox=-7.0,53.0,-6.0,53.5

# Import one facility type at a time
python manage.py import_facilities --types=hospital
# Wait a few minutes, then:
python manage.py import_facilities --types=fire_station

# Add limit for testing
python manage.py import_facilities --limit=20
```

**Note**: The command now waits 5 seconds between each facility type query to respect Overpass API rate limits. Full imports will take longer but be more reliable.

### No Data Imported

**Problem**: No results returned from API

**Solutions**:
1. Check your bbox coordinates are correct (west,south,east,north)
2. Verify country name spelling
3. Try OSM Overpass API directly: https://overpass-turbo.eu/

### Duplicate Facilities

**Problem**: Running import multiple times creates duplicates

**Solution**:
```bash
# Always use --clear flag for fresh import
python manage.py import_facilities --clear
```

Or the command uses `update_or_create` to avoid duplicates when possible.

## API Rate Limits

### OpenStreetMap Nominatim
- Limit: 1 request per second
- Our commands: Rate-limited to 1.5 seconds per request
- Usage Policy: https://operations.osmfoundation.org/policies/nominatim/

### Overpass API
- Limit: ~2 concurrent connections
- Our commands: Sequential requests with 2-second delay
- Public instances: Can be slow during peak times

## Alternative Data Sources

### For Ireland Specifically

1. **CSO (Central Statistics Office)**
   - https://data.cso.ie/
   - Official Irish government data

2. **Tailte Éireann (Ordnance Survey Ireland)**
   - https://data.gov.ie/organization/ordnance-survey-ireland
   - Authoritative boundary data

3. **HSE (Health Service Executive)**
   - https://www.hse.ie/eng/services/list/3/acutehospitals/
   - Official healthcare facility data

### Implementing Custom Sources

See the code in `import_facilities.py` and `import_counties.py` - you can add new source methods:

```python
def import_from_custom_api(self, facility_types, options):
    # Your custom import logic here
    pass
```

## Performance Optimization

### Large Imports

For importing large datasets (1000+ facilities):

```bash
# Use transactions (already enabled in commands)
# Import in batches
python manage.py import_facilities --types=hospital --limit=500
python manage.py import_facilities --types=fire_station --limit=500

# Or use spatial indexes (already configured in schema)
```

### Database Indexes

The schema already includes spatial indexes:
- `emergency_facility_geom_idx` - Spatial index on facility locations
- `admin_counties_geom_idx` - Spatial index on county boundaries

## Next Steps

After importing data:

1. **Verify in Django Admin**: http://localhost/admin/
2. **Check the map**: http://localhost/
3. **Test spatial queries**: Try the "within county" or "within radius" features
4. **Customize**: Modify facilities/counties as needed

## Support

For issues with:
- **Commands**: Check Django logs or run with `--verbosity=2`
- **API errors**: Check API status at [status.openstreetmap.org](https://status.openstreetmap.org/)
- **Data quality**: Report issues on OpenStreetMap or use custom GeoJSON

---

**Pro Tip**: Start with a small test import using `--limit=10` to verify everything works before doing a full import!
