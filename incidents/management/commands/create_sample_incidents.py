"""
Management command to create sample incidents and vehicles for testing.
"""
import random
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.contrib.auth import get_user_model
from incidents.models import Incident, Vehicle, DispatcherProfile
from facilities.models import EmergencyFacility

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample incidents and vehicles for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--incidents',
            type=int,
            default=10,
            help='Number of sample incidents to create (default: 10)'
        )
        parser.add_argument(
            '--vehicles',
            type=int,
            default=15,
            help='Number of sample vehicles to create (default: 15)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing incidents and vehicles before creating new ones'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing incidents and vehicles...')
            Incident.objects.all().delete()
            Vehicle.objects.all().delete()

        # Get or create a dispatcher user
        dispatcher_user, created = User.objects.get_or_create(
            username='dispatcher1',
            defaults={
                'email': 'dispatcher1@example.com',
                'first_name': 'Test',
                'last_name': 'Dispatcher',
                'is_staff': True
            }
        )
        if created:
            dispatcher_user.set_password('dispatcher123')
            dispatcher_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created dispatcher user: dispatcher1'))

        # Create dispatcher profile
        DispatcherProfile.objects.get_or_create(
            user=dispatcher_user,
            defaults={
                'badge_number': 'D-001',
                'is_on_duty': True
            }
        )

        # Get fire stations for vehicle home stations
        fire_stations = list(EmergencyFacility.objects.filter(type='fire_station')[:20])
        ambulance_bases = list(EmergencyFacility.objects.filter(type='ambulance_base')[:20])
        police_stations = list(EmergencyFacility.objects.filter(type='police_station')[:20])

        if not fire_stations and not ambulance_bases and not police_stations:
            self.stdout.write(self.style.WARNING('No facilities found. Creating vehicles without home stations.'))

        # Sample locations around Ireland (Dublin area + Cork + Galway + Limerick)
        sample_locations = [
            # Dublin area
            {'lat': 53.3498, 'lon': -6.2603, 'area': 'Dublin City Centre'},
            {'lat': 53.3244, 'lon': -6.2514, 'area': 'Dublin South'},
            {'lat': 53.3778, 'lon': -6.2452, 'area': 'Dublin North'},
            {'lat': 53.3389, 'lon': -6.1784, 'area': 'Dublin Docklands'},
            {'lat': 53.3533, 'lon': -6.3200, 'area': 'Phoenix Park'},
            # Cork
            {'lat': 51.8969, 'lon': -8.4863, 'area': 'Cork City'},
            {'lat': 51.9000, 'lon': -8.4700, 'area': 'Cork East'},
            # Galway
            {'lat': 53.2707, 'lon': -9.0568, 'area': 'Galway City'},
            {'lat': 53.2800, 'lon': -9.0400, 'area': 'Galway North'},
            # Limerick
            {'lat': 52.6680, 'lon': -8.6305, 'area': 'Limerick City'},
        ]

        # Incident types and priorities
        incident_types = ['fire', 'medical', 'crime', 'traffic', 'hazmat', 'rescue', 'other']
        priorities = ['critical', 'high', 'medium', 'low']
        statuses = ['pending', 'dispatched', 'en_route', 'on_scene', 'resolved']

        # Create vehicles
        self.stdout.write(f'Creating {options["vehicles"]} sample vehicles...')
        vehicles_created = 0
        vehicle_prefixes = {
            'fire': ['FE', 'FT', 'FL'],  # Fire Engine, Fire Truck, Fire Ladder
            'ambulance': ['AM', 'AL', 'AR'],  # Ambulance, Advanced Life Support, Ambulance Rescue
            'police': ['PC', 'PI', 'PV'],  # Police Car, Police Interceptor, Police Van
            'rescue': ['RU', 'RT'],  # Rescue Unit, Rescue Team
        }

        for i in range(options['vehicles']):
            vehicle_type = random.choice(['fire', 'ambulance', 'police', 'rescue'])
            prefix = random.choice(vehicle_prefixes[vehicle_type])
            call_sign = f'{prefix}-{random.randint(100, 999)}'
            
            # Check if call sign already exists
            if Vehicle.objects.filter(call_sign=call_sign).exists():
                continue

            # Select home station based on vehicle type
            home_station = None
            if vehicle_type == 'fire' and fire_stations:
                home_station = random.choice(fire_stations)
            elif vehicle_type == 'ambulance' and ambulance_bases:
                home_station = random.choice(ambulance_bases)
            elif vehicle_type == 'police' and police_stations:
                home_station = random.choice(police_stations)

            # Create vehicle at home station or random location
            if home_station:
                location = home_station.geom
            else:
                loc = random.choice(sample_locations)
                # Add small random offset
                location = Point(
                    loc['lon'] + random.uniform(-0.01, 0.01),
                    loc['lat'] + random.uniform(-0.01, 0.01),
                    srid=4326
                )

            Vehicle.objects.create(
                call_sign=call_sign,
                vehicle_type=vehicle_type,
                status=random.choice(['available', 'available', 'available', 'dispatched', 'on_scene']),
                current_location=location,
                home_station=home_station
            )
            vehicles_created += 1

        self.stdout.write(self.style.SUCCESS(f'Created {vehicles_created} vehicles'))

        # Create incidents
        self.stdout.write(f'Creating {options["incidents"]} sample incidents...')
        incidents_created = 0

        incident_titles = {
            'fire': [
                'House fire reported',
                'Commercial building fire',
                'Vehicle fire on motorway',
                'Kitchen fire in apartment',
                'Warehouse fire alarm'
            ],
            'medical': [
                'Cardiac arrest',
                'Traffic accident with injuries',
                'Person collapsed',
                'Breathing difficulties reported',
                'Fall victim - elderly person'
            ],
            'crime': [
                'Burglary in progress',
                'Assault reported',
                'Suspicious activity',
                'Domestic disturbance',
                'Robbery alarm activated'
            ],
            'traffic': [
                'Multiple vehicle collision',
                'Pedestrian struck',
                'Vehicle vs cyclist',
                'Highway obstruction',
                'Overturned vehicle'
            ],
            'hazmat': [
                'Chemical spill reported',
                'Gas leak detected',
                'Fuel tanker incident',
                'Industrial accident'
            ],
            'rescue': [
                'Person trapped in vehicle',
                'Water rescue required',
                'Person stuck in elevator',
                'Structural collapse'
            ],
            'other': [
                'General assistance required',
                'Animal rescue',
                'Public safety concern'
            ]
        }

        for i in range(options['incidents']):
            incident_type = random.choice(incident_types)
            priority = random.choices(
                priorities, 
                weights=[5, 20, 50, 25],  # Favor medium priority
                k=1
            )[0]
            status = random.choices(
                statuses,
                weights=[30, 20, 15, 20, 15],  # Favor pending
                k=1
            )[0]

            loc = random.choice(sample_locations)
            location = Point(
                loc['lon'] + random.uniform(-0.02, 0.02),
                loc['lat'] + random.uniform(-0.02, 0.02),
                srid=4326
            )

            title = random.choice(incident_titles.get(incident_type, incident_titles['other']))

            incident = Incident.objects.create(
                incident_type=incident_type,
                priority=priority,
                status=status,
                title=f'{title} - {loc["area"]}',
                description=f'Sample incident for testing. Location: {loc["area"]}.',
                location=location,
                reporter_name='Automated Test',
                reporter_phone='999'
            )
            incidents_created += 1

        self.stdout.write(self.style.SUCCESS(f'Created {incidents_created} incidents'))

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Sample data creation complete!'))
        self.stdout.write(f'  Incidents: {Incident.objects.count()}')
        self.stdout.write(f'  Vehicles: {Vehicle.objects.count()}')
        self.stdout.write(f'  Dispatcher user: dispatcher1 / dispatcher123')
