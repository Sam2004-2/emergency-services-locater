"""
Seed the database with data from OpenStreetMap APIs.

This command imports:
- Irish county boundaries from OSM Nominatim API
- Emergency facilities (hospitals, fire stations, police, ambulance bases) from OSM Overpass API

Usage:
    python manage.py seed_database
    python manage.py seed_database --clear
    python manage.py seed_database --counties-only
    python manage.py seed_database --facilities-only
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Seed the database with Irish counties and emergency facilities from OpenStreetMap'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )
        parser.add_argument(
            '--counties-only',
            action='store_true',
            help='Only import county boundaries',
        )
        parser.add_argument(
            '--facilities-only',
            action='store_true',
            help='Only import emergency facilities',
        )
        parser.add_argument(
            '--bbox',
            type=str,
            default='-10.5,51.4,-5.4,55.4',
            help='Bounding box for facilities (default: Ireland)',
        )

    def handle(self, *args, **options):
        clear = options['clear']
        counties_only = options['counties_only']
        facilities_only = options['facilities_only']
        bbox = options['bbox']

        self.stdout.write(self.style.NOTICE('=' * 60))
        self.stdout.write(self.style.NOTICE('Starting database seeding from OpenStreetMap APIs'))
        self.stdout.write(self.style.NOTICE('=' * 60))

        # Import counties
        if not facilities_only:
            self.stdout.write(self.style.NOTICE('\n📍 Importing Irish county boundaries...'))
            county_args = ['--source=osm']
            if clear:
                county_args.append('--clear')
            
            try:
                call_command('import_counties', *county_args)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Failed to import counties: {e}'))

        # Import facilities
        if not counties_only:
            self.stdout.write(self.style.NOTICE('\n🏥 Importing emergency facilities...'))
            facility_args = [
                '--source=osm',
                f'--bbox={bbox}',
                '--types=hospital,fire_station,police_station,ambulance_base',
            ]
            if clear:
                facility_args.append('--clear')
            
            try:
                call_command('import_facilities', *facility_args)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Failed to import facilities: {e}'))

        self.stdout.write(self.style.NOTICE('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('✓ Database seeding complete!'))
        self.stdout.write(self.style.NOTICE('=' * 60))

        # Print summary
        from boundaries.models import County
        from services.models import EmergencyFacility
        
        self.stdout.write(f'\nDatabase Summary:')
        self.stdout.write(f'  Counties: {County.objects.count()}')
        self.stdout.write(f'  Emergency Facilities: {EmergencyFacility.objects.count()}')
        for ftype, label in EmergencyFacility._meta.get_field('type').choices:
            count = EmergencyFacility.objects.filter(type=ftype).count()
            self.stdout.write(f'    - {label}: {count}')
