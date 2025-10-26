#!/usr/bin/env python
"""
Test and fix county import by trying different Nominatim queries
"""
import os
import django
import requests
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'es_locator.settings')
django.setup()

from boundaries.models import County
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from django.db.models import Max

def test_nominatim_query(query_string):
    """Test different query formats to find county boundaries"""
    print(f"\nTesting query: '{query_string}'")
    
    params = {
        'q': query_string,
        'format': 'geojson',
        'polygon_geojson': 1,
        'limit': 5,
    }
    
    response = requests.get(
        'https://nominatim.openstreetmap.org/search',
        params=params,
        headers={'User-Agent': 'EmergencyServicesLocator/1.0'},
        timeout=10
    )
    
    data = response.json()
    
    if data.get('features'):
        for idx, feature in enumerate(data['features'][:3]):
            props = feature.get('properties', {})
            geom = feature.get('geometry')
            print(f"\n  Result {idx+1}:")
            print(f"    Display name: {props.get('display_name', 'N/A')[:80]}")
            print(f"    OSM Type: {props.get('osm_type')}")
            print(f"    Type: {props.get('type')}")
            print(f"    Geom type: {geom.get('type') if geom else 'None'}")
            if geom:
                g = GEOSGeometry(str(geom))
                print(f"    Area: {g.area:.6f} sq degrees")
                print(f"    Coords: {g.num_coords}")
    else:
        print("  No results")
    
    return data

# Test different query formats for Dublin
print("=" * 60)
print("TESTING DIFFERENT QUERY FORMATS FOR DUBLIN")
print("=" * 60)

queries = [
    "Dublin County, Ireland",
    "County Dublin, Ireland",
    "Dublin, Ireland",
    "Baile Átha Cliath, Ireland",
]

results = {}
for query in queries:
    results[query] = test_nominatim_query(query)
    time.sleep(2)  # Rate limiting

print("\n" + "=" * 60)
print("RECOMMENDATION")
print("=" * 60)

# Find the best result (largest area with type=administrative)
best_query = None
best_area = 0
best_feature = None

for query, data in results.items():
    if data.get('features'):
        for feature in data['features']:
            props = feature.get('properties', {})
            geom = feature.get('geometry')
            if geom and props.get('type') in ['administrative', 'boundary']:
                g = GEOSGeometry(str(geom))
                if g.area > best_area:
                    best_area = g.area
                    best_query = query
                    best_feature = feature

if best_feature:
    print(f"\nBest query: '{best_query}'")
    print(f"Area: {best_area:.6f} sq degrees")
    print(f"Display: {best_feature['properties'].get('display_name', 'N/A')}")
    
    # Try to import it
    print("\nAttempting to import Dublin with this geometry...")
    try:
        geom = GEOSGeometry(str(best_feature['geometry']))
        if geom.geom_type == 'Polygon':
            geom = MultiPolygon(geom)
        
        # Update Dublin
        dublin = County.objects.get(id=1)
        dublin.geom = geom
        dublin.save()
        
        print(f"✅ Updated Dublin successfully!")
        print(f"   New area: {dublin.geom.area:.6f} sq degrees")
        print(f"   New bounds: {dublin.geom.extent}")
        
        # Test with a facility
        from services.models import EmergencyFacility
        within = EmergencyFacility.objects.filter(geom__within=dublin.geom).count()
        print(f"   Facilities now within Dublin: {within}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("\nNo suitable boundary found!")
