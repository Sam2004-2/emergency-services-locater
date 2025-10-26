#!/usr/bin/env python
"""
Test which query format works best for each Irish county
"""
import os
import django
import requests
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'es_locator.settings')
django.setup()

from boundaries.models import County
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon

def test_query_formats(county_name):
    """Test different query formats for a county"""
    
    query_formats = [
        f"County {county_name}, Ireland",
        f"{county_name}, Ireland",
        f"County {county_name}, Leinster, Ireland",
        f"County {county_name}, Munster, Ireland",
        f"County {county_name}, Connacht, Ireland",
        f"County {county_name}, Ulster, Ireland",
    ]
    
    best_result = None
    best_area = 0
    best_query = None
    
    for query in query_formats:
        try:
            params = {
                'q': query,
                'format': 'geojson',
                'polygon_geojson': 1,
                'limit': 3,
            }
            
            response = requests.get(
                'https://nominatim.openstreetmap.org/search',
                params=params,
                headers={'User-Agent': 'EmergencyServicesLocator/1.0'},
                timeout=10
            )
            
            data = response.json()
            
            if data.get('features'):
                for feature in data['features']:
                    props = feature.get('properties', {})
                    geom_data = feature.get('geometry')
                    
                    # Look for administrative boundaries
                    if props.get('type') in ['administrative', 'boundary'] and geom_data:
                        geom = GEOSGeometry(str(geom_data))
                        if geom.area > best_area:
                            best_area = geom.area
                            best_result = feature
                            best_query = query
            
            time.sleep(1.5)  # Rate limiting
            
        except Exception as e:
            print(f"  Error with query '{query}': {e}")
            continue
    
    return best_query, best_result, best_area

# Test a few problematic counties
test_counties = ['Cork', 'Galway', 'Kerry', 'Mayo', 'Wicklow']

print("Testing query formats for problematic counties...")
print("=" * 70)

for county_name in test_counties:
    print(f"\n{county_name}:")
    best_query, best_result, best_area = test_query_formats(county_name)
    
    if best_result:
        print(f"  ✅ Best query: '{best_query}'")
        print(f"     Area: {best_area:.6f} sq degrees")
        print(f"     Display: {best_result['properties'].get('display_name', 'N/A')[:80]}")
    else:
        print(f"  ❌ No suitable result found")

print("\n" + "=" * 70)
print("\nConclusion:")
print("The 'County X, Ireland' format doesn't work consistently.")
print("Alternative: Use OSM relation IDs directly or improve query logic.")
