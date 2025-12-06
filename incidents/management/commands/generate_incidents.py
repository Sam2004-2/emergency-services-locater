"""Generate random demo incidents for testing."""
import random
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from incidents.models import Incident
from services.models import EmergencyFacility


class Command(BaseCommand):
    help = 'Generate random demo incidents around Ireland'

    INCIDENT_TITLES = {
        'fire': [
            'House Fire on Main Street',
            'Vehicle Fire on Motorway',
            'Warehouse Fire Reported',
            'Chimney Fire in Residential Area',
            'Brush Fire Near Park',
        ],
        'medical': [
            'Cardiac Emergency',
            'Traffic Accident with Injuries',
            'Person Collapsed in Public',
            'Breathing Difficulties Reported',
            'Severe Allergic Reaction',
        ],
        'crime': [
            'Break-in Reported',
            'Assault in Progress',
            'Suspicious Activity',
            'Vehicle Theft',
            'Robbery at Shop',
        ],
        'accident': [
            'Multi-Vehicle Collision',
            'Pedestrian Hit by Car',
            'Motorcycle Accident',
            'Rear-End Collision',
            'Vehicle Rolled Over',
        ],
    }

    DUBLIN_AREAS = [
        ('Dublin City Centre', 53.3498, -6.2603),
        ('Ballymun', 53.3957, -6.2640),
        ('Tallaght', 53.2858, -6.3733),
        ('Blanchardstown', 53.3877, -6.3751),
        ('Dún Laoghaire', 53.2944, -6.1333),
        ('Clondalkin', 53.3217, -6.3950),
        ('Swords', 53.4597, -6.2181),
        ('Rathfarnham', 53.3011, -6.2850),
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of incidents to generate',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing incidents first',
        )

    def handle(self, *args, **options):
        count = options['count']
        clear = options['clear']

        if clear:
            deleted = Incident.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f'Deleted {deleted[0]} existing incidents')
            )

        # Get or create demo user
        user, created = User.objects.get_or_create(
            username='demo_dispatcher',
            defaults={
                'email': 'demo@example.com',
                'first_name': 'Demo',
                'last_name': 'Dispatcher',
            }
        )
        if created:
            user.set_password('demo123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created demo user: {user.username}'))

        # Generate incidents
        created_count = 0
        for _ in range(count):
            incident_type = random.choice(['fire', 'medical', 'crime', 'accident'])
            severity = random.choice(['low', 'medium', 'high', 'critical'])
            status = random.choice(['pending', 'dispatched', 'en_route', 'on_scene'])
            
            # Random location in Dublin area
            area_name, base_lat, base_lng = random.choice(self.DUBLIN_AREAS)
            lat = base_lat + random.uniform(-0.02, 0.02)
            lng = base_lng + random.uniform(-0.02, 0.02)
            location = Point(lng, lat, srid=4326)

            # Random title
            title = random.choice(self.INCIDENT_TITLES[incident_type])
            
            # Find nearest facility
            facility_type_map = {
                'fire': 'fire_station',
                'medical': 'hospital',
                'crime': 'police_station',
                'accident': 'hospital'
            }
            facility_type = facility_type_map[incident_type]
            nearest_facility = EmergencyFacility.objects.filter(
                facility_type=facility_type
            ).nearest(location, limit=1).first()

            incident = Incident.objects.create(
                title=title,
                description=f'Demo {incident_type} incident near {area_name}',
                incident_type=incident_type,
                severity=severity,
                status=status,
                location=location,
                address=f'{area_name}, Dublin, Ireland',
                reported_by=user,
                nearest_facility=nearest_facility,
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully generated {created_count} incidents')
        )
