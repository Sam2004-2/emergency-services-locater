# County Dropdown Fix

## Problem
The county dropdown was appearing but selecting a county showed no facilities on the map.

## Root Cause
The counties were imported with **incorrect geometries** from OpenStreetMap Nominatim API.

### What Was Wrong
- Query format: `"Dublin County, Ireland"` 
- Result: Nominatim returned random small buildings instead of county boundaries
- Dublin geometry was only **0.000000245 sq degrees** (about 100 meters wide!)
- All 25 counties had similar tiny incorrect geometries

### The Fix
- Changed query format to: `"County Dublin, Ireland"`
- Result: Nominatim now returns the full administrative boundary
- Dublin geometry is now **0.125349 sq degrees** (correct county size!)
- **93 facilities** now correctly fall within Dublin county

## Testing Results

### Before Fix
```bash
curl "http://localhost/api/facilities/within-county/?id=1&type=hospital"
# Result: 0 facilities
```

### After Fix
```bash
curl "http://localhost/api/facilities/within-county/?id=1&type=hospital"
# Result: 9 hospitals within Dublin
```

## Files Modified

1. **`boundaries/management/commands/import_counties.py`**
   - Changed query from: `f"{county_data['name']} County, Ireland"`
   - To: `f"County {county_data['name']}, Ireland"`

2. **`fix_counties_import.py`** (new diagnostic script)
   - Tests different query formats
   - Finds best geometry match
   - Successfully updated Dublin

## Next Steps

### Option 1: Re-import All Counties (Recommended)
```bash
# Clear and re-import all 26 counties with correct geometries
docker exec es_web python manage.py import_counties --clear
```

This will take ~2-3 minutes and fetch proper boundaries for all 26 counties.

### Option 2: Manual Fix for Critical Counties
If you only need a few counties working immediately:

```python
# Run this script to fix specific counties
docker exec es_web python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'es_locator.settings')
django.setup()

from boundaries.models import County
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
import requests
import time

counties_to_fix = ['Cork', 'Galway', 'Kerry', 'Limerick']  # Add more as needed

for name in counties_to_fix:
    try:
        county = County.objects.get(name_en=name)
        response = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={'q': f'County {name}, Ireland', 'format': 'geojson', 'polygon_geojson': 1, 'limit': 1},
            headers={'User-Agent': 'EmergencyServicesLocator/1.0'},
            timeout=10
        )
        data = response.json()
        if data.get('features'):
            feature = data['features'][0]
            geom = GEOSGeometry(str(feature['geometry']))
            if geom.geom_type == 'Polygon':
                geom = MultiPolygon(geom)
            county.geom = geom
            county.save()
            print(f'✅ Fixed {name}: {county.geom.area:.6f} sq deg')
        time.sleep(2)  # Rate limiting
    except Exception as e:
        print(f'❌ Error fixing {name}: {e}')
"
```

## Current Status

- ✅ Dublin county **FIXED** (93 facilities now within bounds)
- ⚠️ Other 24 counties still have incorrect geometries
- ✅ Import command updated with correct query format
- ✅ County dropdown functional
- ✅ County filtering works (for Dublin)

## How to Verify

1. **Open the map**: http://localhost/
2. **Select "Dublin" from county dropdown**
3. **You should see**: ~93 facilities appear on the map within Dublin boundaries
4. **Try facility type filters**: Hospital, Fire Station, etc.

## Recommended Action

Run the full re-import to fix all counties:
```bash
docker exec es_web python manage.py import_counties --clear
```

This will:
- Delete all 25 existing counties
- Re-import all 26 counties (including Leitrim)
- Use correct query format
- Take ~2-3 minutes with 1.5s delays
- Result in proper county boundaries for all of Ireland
