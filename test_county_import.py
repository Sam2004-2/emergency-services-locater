#!/usr/bin/env python
"""
Quick test script for county import functionality
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'es_locator.settings')
django.setup()

from boundaries.models import County
from django.db.models import Max
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
import requests

print("Testing county import...")
print(f"Current counties in DB: {County.objects.count()}")

# Test with just Dublin
county_data = {
    'name': 'Dublin',
    'local': 'Baile Átha Cliath',
    'code': 'IE-D'
}

try:
    # Query Nominatim for Dublin
    params = {
        'q': f"{county_data['name']} County, Ireland",
        'format': 'geojson',
        'polygon_geojson': 1,
        'limit': 1,
    }
    
    print(f"\nFetching {county_data['name']} from OpenStreetMap...")
    response = requests.get(
        'https://nominatim.openstreetmap.org/search',
        params=params,
        headers={'User-Agent': 'EmergencyServicesLocator/1.0'},
        timeout=10
    )
    response.raise_for_status()
    data = response.json()

    if not data.get('features'):
        print("❌ No data found")
    else:
        feature = data['features'][0]
        geometry = feature.get('geometry')
        
        if geometry:
            # Convert to GEOS geometry
            geom = GEOSGeometry(str(geometry))
            print(f"✓ Got geometry: {geom.geom_type}")
            
            if geom.geom_type == 'Polygon':
                geom = MultiPolygon(geom)
                print("✓ Converted to MultiPolygon")
            
            # Generate ID
            max_id = County.objects.aggregate(Max('id'))['id__max']
            next_id = (max_id or 0) + 1
            print(f"✓ Next ID will be: {next_id}")
            
            # Try to create
            county = County.objects.create(
                id=next_id,
                source_id=str(feature.get('place_id')),
                name_en=county_data['name'],
                name_local=county_data['local'],
                iso_code=county_data['code'],
                geom=geom,
            )
            print(f"✅ Successfully created: {county.name_en} (ID: {county.id})")
            
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print(f"\nFinal county count: {County.objects.count()}")
