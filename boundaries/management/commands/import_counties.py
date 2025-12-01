"""
Import Irish county boundaries from OpenStreetMap Nominatim API.

Usage:
    python manage.py import_counties
    python manage.py import_counties --source=osm
    python manage.py import_counties --source=geojson --url=<URL>
    python manage.py import_counties --clear
"""

import requests
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import GEOSGeometry
from django.db import transaction
from django.db.models import Max
from boundaries.models import County


class Command(BaseCommand):
    help = 'Import Irish county boundaries from open data APIs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            default='osm',
            choices=['osm', 'geojson'],
            help='Data source: osm (OpenStreetMap) or geojson (custom URL)',
        )
        parser.add_argument(
            '--url',
            type=str,
            help='Custom GeoJSON URL (used with --source=geojson)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing counties before importing',
        )

    def handle(self, *args, **options):
        if options['clear']:
            count = County.objects.count()
            County.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {count} existing counties'))

        source = options['source']
        
        if source == 'osm':
            self.import_from_osm()
        elif source == 'geojson':
            url = options['url']
            if not url:
                self.stderr.write(self.style.ERROR('--url is required when using --source=geojson'))
                return
            self.import_from_geojson(url)

    def import_from_osm(self):
        """
        Import counties using OpenStreetMap Nominatim API.
        This fetches simplified boundaries for Irish counties.
        """
        self.stdout.write('Fetching Irish counties from OpenStreetMap...')
        
        # List of Irish counties
        counties = [
            {'name': 'Dublin', 'local': 'Baile Átha Cliath', 'code': 'IE-D'},
            {'name': 'Cork', 'local': 'Corcaigh', 'code': 'IE-CO'},
            {'name': 'Galway', 'local': 'Gaillimh', 'code': 'IE-G'},
            {'name': 'Wicklow', 'local': 'Cill Mhantáin', 'code': 'IE-WW'},
            {'name': 'Kerry', 'local': 'Ciarraí', 'code': 'IE-KY'},
            {'name': 'Limerick', 'local': 'Luimneach', 'code': 'IE-LK'},
            {'name': 'Mayo', 'local': 'Maigh Eo', 'code': 'IE-MO'},
            {'name': 'Donegal', 'local': 'Dún na nGall', 'code': 'IE-DL'},
            {'name': 'Tipperary', 'local': 'Tiobraid Árann', 'code': 'IE-TA'},
            {'name': 'Clare', 'local': 'An Clár', 'code': 'IE-CE'},
            {'name': 'Wexford', 'local': 'Loch Garman', 'code': 'IE-WX'},
            {'name': 'Waterford', 'local': 'Port Láirge', 'code': 'IE-WD'},
            {'name': 'Kilkenny', 'local': 'Cill Chainnigh', 'code': 'IE-KK'},
            {'name': 'Meath', 'local': 'An Mhí', 'code': 'IE-MH'},
            {'name': 'Kildare', 'local': 'Cill Dara', 'code': 'IE-KE'},
            {'name': 'Sligo', 'local': 'Sligeach', 'code': 'IE-SO'},
            {'name': 'Louth', 'local': 'Lú', 'code': 'IE-LH'},
            {'name': 'Westmeath', 'local': 'An Iarmhí', 'code': 'IE-WH'},
            {'name': 'Offaly', 'local': 'Uíbh Fhailí', 'code': 'IE-OY'},
            {'name': 'Laois', 'local': 'Laois', 'code': 'IE-LS'},
            {'name': 'Carlow', 'local': 'Ceatharlach', 'code': 'IE-CW'},
            {'name': 'Cavan', 'local': 'An Cabhán', 'code': 'IE-CN'},
            {'name': 'Monaghan', 'local': 'Muineachán', 'code': 'IE-MN'},
            {'name': 'Longford', 'local': 'An Longfort', 'code': 'IE-LD'},
            {'name': 'Roscommon', 'local': 'Ros Comáin', 'code': 'IE-RN'},
            {'name': 'Leitrim', 'local': 'Liatroim', 'code': 'IE-LM'},
        ]

        created_count = 0
        failed_count = 0

        with transaction.atomic():
            for idx, county_data in enumerate(counties, start=1):
                try:
                    # Query Nominatim for the county boundary
                    # Use "County X" format to get administrative boundaries, not "X County"
                    # Request multiple results to find the best match
                    params = {
                        'q': f"County {county_data['name']}, Ireland",
                        'format': 'geojson',
                        'polygon_geojson': 1,
                        'limit': 5,  # Get multiple results to find the best
                    }
                    # Make the request to OSM to populate county boundary
                    response = requests.get(
                        'https://nominatim.openstreetmap.org/search',
                        params=params,
                        headers={'User-Agent': 'EmergencyServicesLocator/1.0'},
                        timeout=10
                    )
                    response.raise_for_status()
                    data = response.json()

                    if not data.get('features'):
                        self.stderr.write(
                            self.style.WARNING(f"No data found for {county_data['name']}")
                        )
                        failed_count += 1
                        continue

                    # Find the best result (largest area with type=administrative)
                    best_feature = None
                    best_area = 0
                    
                    for feature in data['features']:
                        props = feature.get('properties', {})
                        geometry = feature.get('geometry')
                        
                        # Look for administrative boundaries
                        if geometry and props.get('type') in ['administrative', 'boundary']:
                            geom = GEOSGeometry(str(geometry))
                            # County boundaries should be at least 0.01 sq degrees
                            if geom.area > best_area and geom.area > 0.01:
                                best_area = geom.area
                                best_feature = feature
                    
                    # If no administrative boundary found, fall back to first result
                    if not best_feature:
                        best_feature = data['features'][0]
                        geometry = best_feature.get('geometry')
                        if not geometry:
                            self.stderr.write(
                                self.style.WARNING(f"No geometry for {county_data['name']}")
                            )
                            failed_count += 1
                            continue
                    
                    geometry = best_feature.get('geometry')
                    if not geometry:
                        self.stderr.write(
                            self.style.WARNING(f"No geometry for {county_data['name']}")
                        )
                        failed_count += 1
                        continue

                    # Convert to GEOS geometry and ensure it's MultiPolygon
                    geom = GEOSGeometry(str(geometry))
                    if geom.geom_type == 'Polygon':
                        from django.contrib.gis.geos import MultiPolygon
                        geom = MultiPolygon(geom)

                    # Check if county exists
                    existing = County.objects.filter(iso_code=county_data['code']).first()
                    
                    if existing:
                        # Update existing county
                        existing.source_id = best_feature.get('place_id') or best_feature.get('properties', {}).get('place_id')
                        existing.name_en = county_data['name']
                        existing.name_local = county_data['local']
                        existing.geom = geom
                        existing.save()
                    else:
                        # Generate new ID for unmanaged model
                        max_id = County.objects.aggregate(Max('id'))['id__max']
                        next_id = (max_id or 0) + 1
                        
                        # Create new county with explicit ID
                        County.objects.create(
                            id=next_id,
                            source_id=best_feature.get('place_id') or best_feature.get('properties', {}).get('place_id'),
                            name_en=county_data['name'],
                            name_local=county_data['local'],
                            iso_code=county_data['code'],
                            geom=geom,
                        )
                    
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ {county_data['name']} ({created_count}/{len(counties)})")
                    )
                    
                    # Rate limiting - be nice to OSM servers
                    import time
                    time.sleep(1.5)

                except Exception as e:
                    self.stderr.write(
                        self.style.ERROR(f"✗ Failed to import {county_data['name']}: {str(e)}")
                    )
                    failed_count += 1
                    continue

        self.stdout.write(
            self.style.SUCCESS(
                f'\nImport complete: {created_count} counties imported, {failed_count} failed'
            )
        )

    def import_from_geojson(self, url):
        """Import counties from a GeoJSON URL"""
        self.stdout.write(f'Fetching data from {url}...')
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get('type') != 'FeatureCollection':
                self.stderr.write(self.style.ERROR('Invalid GeoJSON: not a FeatureCollection'))
                return

            features = data.get('features', [])
            created_count = 0

            with transaction.atomic():
                for idx, feature in enumerate(features, start=1):
                    try:
                        props = feature.get('properties', {})
                        geometry = feature.get('geometry')

                        if not geometry:
                            continue

                        # Try to extract county name from various possible fields
                        name = (props.get('NAME_TAG') or 
                               props.get('name') or 
                               props.get('NAME') or
                               props.get('COUNTYNAME') or
                               f'County {idx}')

                        geom = GEOSGeometry(str(geometry))
                        if geom.geom_type == 'Polygon':
                            from django.contrib.gis.geos import MultiPolygon
                            geom = MultiPolygon(geom)

                        # Generate sequential ID for unmanaged model
                        max_id = County.objects.aggregate(Max('id'))['id__max']
                        next_id = (max_id or 0) + 1

                        County.objects.create(
                            id=next_id,
                            source_id=props.get('id', f'geojson_{idx}'),
                            name_en=name,
                            name_local=props.get('name_local', ''),
                            iso_code=props.get('iso_code', ''),
                            geom=geom,
                        )
                        
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(f"✓ {name}"))

                    except Exception as e:
                        self.stderr.write(
                            self.style.ERROR(f"✗ Failed to import feature {idx}: {str(e)}")
                        )
                        continue

            self.stdout.write(
                self.style.SUCCESS(f'\nImported {created_count} counties from GeoJSON')
            )

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Failed to fetch GeoJSON: {str(e)}'))
