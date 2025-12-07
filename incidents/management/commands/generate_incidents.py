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

    # Dublin areas
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

    # Major cities and towns across Ireland
    IRELAND_LOCATIONS = [
        # Dublin Region
        ('Dublin City Centre', 53.3498, -6.2603),
        ('Ballymun', 53.3957, -6.2640),
        ('Tallaght', 53.2858, -6.3733),
        ('Blanchardstown', 53.3877, -6.3751),
        ('Dún Laoghaire', 53.2944, -6.1333),
        ('Swords', 53.4597, -6.2181),
        ('Bray', 53.2029, -6.0987),
        ('Howth', 53.3876, -6.0654),

        # Cork Region
        ('Cork City', 51.8985, -8.4756),
        ('Cobh', 51.8509, -8.2966),
        ('Ballincollig', 51.8881, -8.5877),
        ('Carrigaline', 51.8140, -8.3929),
        ('Midleton', 51.9145, -8.1754),

        # Galway Region
        ('Galway City', 53.2707, -9.0568),
        ('Salthill', 53.2598, -9.0742),
        ('Oranmore', 53.2687, -8.9261),
        ('Tuam', 53.5143, -8.8556),

        # Limerick Region
        ('Limerick City', 52.6638, -8.6267),
        ('Ennis', 52.8432, -8.9861),
        ('Shannon', 52.7036, -8.8640),
        ('Nenagh', 52.8618, -8.1968),

        # Waterford Region
        ('Waterford City', 52.2593, -7.1128),
        ('Tramore', 52.1620, -7.1491),
        ('Dungarvan', 52.0878, -7.6186),

        # Kilkenny Region
        ('Kilkenny City', 52.6541, -7.2448),
        ('Carlow', 52.8365, -6.9341),

        # Kerry Region
        ('Killarney', 52.0590, -9.5044),
        ('Tralee', 52.2704, -9.7026),
        ('Kenmare', 51.8797, -9.5833),

        # Mayo/Sligo Region
        ('Sligo', 54.2697, -8.4694),
        ('Westport', 53.8007, -9.5180),
        ('Castlebar', 53.7610, -9.2981),

        # Donegal Region
        ('Letterkenny', 54.9558, -7.7342),
        ('Donegal Town', 54.6540, -8.1099),
        ('Bundoran', 54.4783, -8.2797),

        # Midlands
        ('Athlone', 53.4239, -7.9407),
        ('Mullingar', 53.5259, -7.3400),
        ('Tullamore', 53.2739, -7.4894),
        ('Portlaoise', 53.0343, -7.2993),
        ('Longford', 53.7275, -7.7933),

        # East Coast
        ('Drogheda', 53.7189, -6.3560),
        ('Dundalk', 54.0037, -6.4158),
        ('Navan', 53.6528, -6.6819),
        ('Arklow', 52.7939, -6.1624),
        ('Wicklow', 52.9808, -6.0445),
        ('Wexford', 52.3369, -6.4633),

        # West Coast
        ('Clifden', 53.4893, -10.0185),
        ('Ballina', 54.1171, -9.1560),
        ('Roscommon', 53.6279, -8.1893),
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
        parser.add_argument(
            '--nationwide',
            action='store_true',
            help='Generate incidents across all of Ireland (not just Dublin)',
        )

    def handle(self, *args, **options):
        count = options['count']
        clear = options['clear']
        nationwide = options['nationwide']

        # Select locations based on --nationwide flag
        locations = self.IRELAND_LOCATIONS if nationwide else self.DUBLIN_AREAS

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
            
            # Random location from selected areas
            area_name, base_lat, base_lng = random.choice(locations)
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
                type=facility_type
            ).knn_nearest(location, limit=1).first()

            incident = Incident.objects.create(
                title=title,
                description=f'Demo {incident_type} incident near {area_name}',
                incident_type=incident_type,
                severity=severity,
                status=status,
                location=location,
                address=f'{area_name}, Ireland',
                reported_by=user,
                nearest_facility=nearest_facility,
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully generated {created_count} incidents')
        )
