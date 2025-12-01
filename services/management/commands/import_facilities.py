"""
Import emergency services (hospitals, fire stations, police stations, ambulance bases)
from OpenStreetMap Overpass API.

Data sources:
- OpenStreetMap Overpass API (global, high coverage) - primary source
- Custom GeoJSON URLs (optional)

Usage:
    python manage.py import_facilities
    python manage.py import_facilities --country=ireland --types=hospital,fire_station
    python manage.py import_facilities --bbox=-10.5,51.4,-5.4,55.4
    python manage.py import_facilities --source=geojson --url=<URL>
    python manage.py import_facilities --clear
"""

import requests
import time
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from services.models import EmergencyFacility


class Command(BaseCommand):
    help = 'Import emergency facilities from open data APIs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            default='osm',
            choices=['osm', 'geojson'],
            help='Data source: osm (OpenStreetMap) or geojson (custom URL)',
        )
        parser.add_argument(
            '--types',
            type=str,
            default='hospital,fire_station,police_station,ambulance_base',
            help='Comma-separated facility types to import',
        )
        parser.add_argument(
            '--country',
            type=str,
            default='ireland',
            help='Country name (used for OSM queries)',
        )
        parser.add_argument(
            '--bbox',
            type=str,
            help='Bounding box: west,south,east,north (e.g., -10.5,51.4,-5.4,55.4 for Ireland)',
        )
        parser.add_argument(
            '--url',
            type=str,
            help='Custom GeoJSON URL (used with --source=geojson)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing facilities before importing',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Maximum number of facilities to import per type',
        )

    def handle(self, *args, **options):
        if options['clear']:
            count = EmergencyFacility.objects.count()
            EmergencyFacility.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {count} existing facilities'))

        facility_types = options['types'].split(',')
        source = options['source']

        if source == 'osm':
            self.import_from_osm(facility_types, options)
        elif source == 'geojson':
            url = options['url']
            if not url:
                self.stderr.write(self.style.ERROR('--url is required when using --source=geojson'))
                return
            self.import_from_geojson(url, facility_types, options)

    def import_from_osm(self, facility_types, options):
        """
        Import facilities using OpenStreetMap Overpass API.
        This provides comprehensive global coverage of emergency services.
        """
        self.stdout.write('Fetching facilities from OpenStreetMap...')

        # Map our types to OSM tags
        osm_queries = {
            'hospital': '[amenity=hospital]',
            'fire_station': '[amenity=fire_station]',
            'police_station': '[amenity=police]',
            'ambulance_base': '[emergency=ambulance_station]',
        }

        # Determine query area
        bbox = options.get('bbox')
        if bbox:
            # Use bounding box
            coords = [float(x) for x in bbox.split(',')]
            area_filter = f'({coords[1]},{coords[0]},{coords[3]},{coords[2]})'
        else:
            # Use country name
            country = options.get('country', 'ireland')
            area_filter = f'(area["name:en"="{country.title()}"])'

        created_count = 0
        total_to_import = len([t for t in facility_types if t in osm_queries])
        current = 0

        for facility_type in facility_types:
            if facility_type not in osm_queries:
                self.stderr.write(
                    self.style.WARNING(f"Unknown facility type: {facility_type}")
                )
                continue

            current += 1
            self.stdout.write(
                self.style.NOTICE(f'\n[{current}/{total_to_import}] Fetching {facility_type}...')
            )

            # Build Overpass query - different syntax for bbox vs area
            if bbox:
                # Direct bbox query without area search
                coords = [float(x) for x in bbox.split(',')]
                query = f"""
                [out:json][timeout:90];
                (
                    node{osm_queries[facility_type]}({coords[1]},{coords[0]},{coords[3]},{coords[2]});
                    way{osm_queries[facility_type]}({coords[1]},{coords[0]},{coords[3]},{coords[2]});
                    relation{osm_queries[facility_type]}({coords[1]},{coords[0]},{coords[3]},{coords[2]});
                );
                out center;
                """
            else:
                # Area-based query for country
                country = options.get('country', 'ireland')
                query = f"""
                [out:json][timeout:90];
                area["name:en"="{country.title()}"]->.searchArea;
                (
                    node{osm_queries[facility_type]}(area.searchArea);
                    way{osm_queries[facility_type]}(area.searchArea);
                    relation{osm_queries[facility_type]}(area.searchArea);
                );
                out center;
                """

            try:
                response = requests.post(
                    'https://overpass-api.de/api/interpreter',
                    data={'data': query},
                    timeout=120  # Increased timeout to 120 seconds to avoid 504 errors
                )
                response.raise_for_status()
                data = response.json()

                elements = data.get('elements', [])
                limit = options.get('limit')
                if limit:
                    elements = elements[:limit]

                type_count = 0
                with transaction.atomic():
                    # Get next available ID
                    max_id = EmergencyFacility.objects.aggregate(
                        Max('id')
                    )['id__max'] or 0
                    next_id = max_id + 1
                    
                    for element in elements:
                        try:
                            tags = element.get('tags', {})
                            
                            # Get coordinates
                            if element.get('type') == 'node':
                                lat = element.get('lat')
                                lon = element.get('lon')
                            elif 'center' in element:
                                lat = element['center'].get('lat')
                                lon = element['center'].get('lon')
                            else:
                                continue

                            if not (lat and lon):
                                continue

                            # Extract facility information
                            name = (tags.get('name') or 
                                   tags.get('official_name') or
                                   tags.get('operator') or
                                   f"{facility_type.replace('_', ' ').title()} {element.get('id')}")

                            address = self._build_address(tags)
                            phone = tags.get('phone') or tags.get('contact:phone')
                            website = tags.get('website') or tags.get('contact:website')

                            # Additional properties
                            properties = {}
                            if facility_type == 'hospital':
                                properties['beds'] = tags.get('beds')
                                properties['emergency'] = tags.get('emergency')
                            if tags.get('operator'):
                                properties['operator'] = tags.get('operator')
                            
                            # Store OSM ID for reference
                            properties['osm_id'] = element.get('id')
                            properties['osm_type'] = element.get('type')

                            # Create facility with sequential ID
                            EmergencyFacility.objects.create(
                                id=next_id,
                                name=name,
                                type=facility_type,
                                address=address,
                                phone=phone,
                                website=website,
                                properties=properties,
                                geom=Point(float(lon), float(lat), srid=4326),
                                created_at=timezone.now(),
                                updated_at=timezone.now(),
                            )
                            
                            next_id += 1
                            type_count += 1
                            created_count += 1

                        except Exception as e:
                            self.stderr.write(
                                self.style.ERROR(f"Failed to import element: {str(e)}")
                            )
                            continue

                self.stdout.write(
                    self.style.SUCCESS(f"✓ Imported {type_count} {facility_type} facilities")
                )

                # Rate limiting - be nice to Overpass API (increased to 5 seconds to avoid 429/504 errors)
                if current < total_to_import:
                    time.sleep(5)

            except requests.exceptions.Timeout:
                self.stderr.write(
                    self.style.ERROR(f"✗ Timeout fetching {facility_type}. Try with --bbox for smaller area.")
                )
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f"✗ Failed to fetch {facility_type}: {str(e)}")
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Total imported: {created_count} facilities')
        )

    def import_from_geojson(self, url, facility_types, options):
        """Import facilities from a GeoJSON URL"""
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
                for feature in features:
                    try:
                        props = feature.get('properties', {})
                        geometry = feature.get('geometry')

                        if not geometry or geometry.get('type') != 'Point':
                            continue

                        coords = geometry.get('coordinates')
                        if not coords or len(coords) < 2:
                            continue

                        # Determine facility type
                        facility_type = props.get('type', 'hospital')
                        if facility_type not in facility_types:
                            continue

                        name = props.get('name', 'Unnamed Facility')

                        EmergencyFacility.objects.create(
                            name=name,
                            type=facility_type,
                            address=props.get('address'),
                            phone=props.get('phone'),
                            website=props.get('website'),
                            properties=props.get('properties', {}),
                            geom=Point(coords[0], coords[1], srid=4326),
                            created_at=timezone.now(),
                            updated_at=timezone.now(),
                        )
                        
                        created_count += 1

                    except Exception as e:
                        continue

            self.stdout.write(
                self.style.SUCCESS(f'\n✓ Imported {created_count} facilities from GeoJSON')
            )

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Failed to fetch GeoJSON: {str(e)}'))

    def _build_address(self, tags):
        """Build address string from OSM tags"""
        parts = []
        
        addr_fields = ['addr:housenumber', 'addr:street', 'addr:city', 'addr:postcode']
        for field in addr_fields:
            if tags.get(field):
                parts.append(tags[field])
        
        return ', '.join(parts) if parts else None
