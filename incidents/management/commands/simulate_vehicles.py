"""Simulate vehicle movements and incident responses."""
import random
import time
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from django.utils import timezone

from incidents.models import Incident, Vehicle


class Command(BaseCommand):
    help = 'Simulate vehicle positions and movements for demo purposes'

    # Major locations across Ireland for vehicle distribution
    IRELAND_BASES = [
        # Dublin Region
        ('Dublin', 53.3498, -6.2603),
        # Cork Region
        ('Cork', 51.8985, -8.4756),
        # Galway Region
        ('Galway', 53.2707, -9.0568),
        # Limerick Region
        ('Limerick', 52.6638, -8.6267),
        # Waterford Region
        ('Waterford', 52.2593, -7.1128),
        # Kilkenny Region
        ('Kilkenny', 52.6541, -7.2448),
        # Kerry Region
        ('Killarney', 52.0590, -9.5044),
        # Sligo Region
        ('Sligo', 54.2697, -8.4694),
        # Donegal Region
        ('Letterkenny', 54.9558, -7.7342),
        # Midlands
        ('Athlone', 53.4239, -7.9407),
        # East Coast
        ('Drogheda', 53.7189, -6.3560),
        ('Dundalk', 54.0037, -6.4158),
        ('Wexford', 52.3369, -6.4633),
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--duration',
            type=int,
            default=60,
            help='Simulation duration in seconds',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=5,
            help='Update interval in seconds',
        )
        parser.add_argument(
            '--create-vehicles',
            action='store_true',
            help='Create demo vehicles if they don\'t exist',
        )
        parser.add_argument(
            '--nationwide',
            action='store_true',
            help='Create vehicles across all of Ireland (not just Dublin)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing vehicles before creating new ones',
        )

    def handle(self, *args, **options):
        duration = options['duration']
        interval = options['interval']
        create_vehicles = options['create_vehicles']
        nationwide = options['nationwide']
        clear = options['clear']

        if clear:
            deleted = Vehicle.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f'Deleted {deleted[0]} existing vehicles')
            )

        if create_vehicles:
            self.create_demo_vehicles(nationwide=nationwide)

        vehicles = Vehicle.objects.all()
        if not vehicles.exists():
            self.stdout.write(
                self.style.ERROR('No vehicles found. Run with --create-vehicles first.')
            )
            return

        self.stdout.write(self.style.SUCCESS(f'Starting simulation with {vehicles.count()} vehicles'))
        self.stdout.write(f'Duration: {duration}s, Interval: {interval}s')
        self.stdout.write('Press Ctrl+C to stop...\n')

        start_time = time.time()
        iteration = 0

        try:
            while time.time() - start_time < duration:
                iteration += 1
                self.stdout.write(f'--- Update #{iteration} ---')

                for vehicle in vehicles:
                    self.update_vehicle_position(vehicle)

                self.stdout.write(self.style.SUCCESS(f'Updated {vehicles.count()} vehicles\n'))
                time.sleep(interval)

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nSimulation stopped by user'))

        self.stdout.write(self.style.SUCCESS('Simulation completed'))

    def create_demo_vehicles(self, nationwide=False):
        """Create demo vehicles across Ireland."""
        from services.models import EmergencyFacility

        facility_type_map = {
            'ambulance': 'hospital',
            'fire_engine': 'fire_station',
            'police_car': 'police_station',
            'helicopter': 'hospital',
        }

        created = 0

        if nationwide:
            # Create vehicles for each major location across Ireland
            for location_name, base_lat, base_lng in self.IRELAND_BASES:
                # Create prefix from location name
                prefix = location_name[:3].upper()

                vehicles_for_location = [
                    (f'{prefix}-AMB-001', 'ambulance', 'available'),
                    (f'{prefix}-FIRE-001', 'fire_engine', 'available'),
                    (f'{prefix}-GARDA-001', 'police_car', 'available'),
                ]

                # Add extra vehicles for major cities
                if location_name in ['Dublin', 'Cork', 'Galway', 'Limerick']:
                    vehicles_for_location.extend([
                        (f'{prefix}-AMB-002', 'ambulance', 'available'),
                        (f'{prefix}-FIRE-002', 'fire_engine', 'available'),
                        (f'{prefix}-GARDA-002', 'police_car', 'available'),
                    ])

                # Dublin gets a helicopter
                if location_name == 'Dublin':
                    vehicles_for_location.append(('DUB-HELI-001', 'helicopter', 'available'))

                for callsign, vehicle_type, status in vehicles_for_location:
                    if not Vehicle.objects.filter(callsign=callsign).exists():
                        # Random position around the base location
                        lat = base_lat + random.uniform(-0.02, 0.02)
                        lng = base_lng + random.uniform(-0.02, 0.02)
                        location = Point(lng, lat, srid=4326)

                        # Find nearest matching facility
                        fac_type = facility_type_map[vehicle_type]
                        base_facility = EmergencyFacility.objects.filter(
                            type=fac_type
                        ).knn_nearest(location, limit=1).first() if EmergencyFacility.objects.filter(
                            type=fac_type
                        ).exists() else None

                        Vehicle.objects.create(
                            callsign=callsign,
                            vehicle_type=vehicle_type,
                            status=status,
                            current_position=location,
                            heading=random.uniform(0, 360),
                            speed_kmh=0,
                            base_facility=base_facility,
                        )
                        created += 1
                        self.stdout.write(f'Created vehicle: {callsign} ({location_name})')
        else:
            # Original Dublin-only behavior
            vehicles_data = [
                ('AMB-001', 'ambulance', 'available'),
                ('AMB-002', 'ambulance', 'available'),
                ('FIRE-001', 'fire_engine', 'available'),
                ('FIRE-002', 'fire_engine', 'available'),
                ('GARDA-001', 'police_car', 'available'),
                ('GARDA-002', 'police_car', 'available'),
                ('HELI-001', 'helicopter', 'available'),
            ]

            for callsign, vehicle_type, status in vehicles_data:
                if not Vehicle.objects.filter(callsign=callsign).exists():
                    # Random position around Dublin
                    lat = 53.3498 + random.uniform(-0.05, 0.05)
                    lng = -6.2603 + random.uniform(-0.05, 0.05)
                    location = Point(lng, lat, srid=4326)

                    fac_type = facility_type_map[vehicle_type]
                    base_facility = EmergencyFacility.objects.filter(
                        type=fac_type
                    ).first()

                    Vehicle.objects.create(
                        callsign=callsign,
                        vehicle_type=vehicle_type,
                        status=status,
                        current_position=location,
                        heading=random.uniform(0, 360),
                        speed_kmh=0,
                        base_facility=base_facility,
                    )
                    created += 1
                    self.stdout.write(f'Created vehicle: {callsign}')

        if created > 0:
            self.stdout.write(self.style.SUCCESS(f'Created {created} demo vehicles\n'))

    def update_vehicle_position(self, vehicle):
        """Simulate vehicle movement."""
        # If vehicle has an active incident, move towards it
        if vehicle.current_incident and vehicle.status in ['dispatched', 'en_route']:
            self.move_towards_incident(vehicle)
        elif vehicle.status == 'on_scene':
            # Stay at incident location
            if vehicle.current_incident:
                vehicle.current_position = vehicle.current_incident.location
                vehicle.speed_kmh = 0
                vehicle.save()
        elif vehicle.status == 'returning':
            # Move back to base
            if vehicle.base_facility:
                self.move_towards_base(vehicle)
            else:
                # No base, mark as available
                vehicle.status = 'available'
                vehicle.speed_kmh = 0
                vehicle.save()
        elif vehicle.status == 'available':
            # Random patrol movement
            self.random_patrol(vehicle)

    def move_towards_incident(self, vehicle):
        """Move vehicle towards incident location."""
        incident = vehicle.current_incident
        current = vehicle.current_position
        target = incident.location

        # Calculate direction
        dx = target.x - current.x
        dy = target.y - current.y
        distance = (dx**2 + dy**2) ** 0.5

        # If close enough, arrive at scene
        if distance < 0.001:  # ~100m
            vehicle.current_position = target
            vehicle.status = 'on_scene'
            vehicle.speed_kmh = 0
            incident.status = 'on_scene'
            incident.save()
            self.stdout.write(f'{vehicle.callsign} arrived at {incident.title}')
        else:
            # Move towards incident (simulate ~60 km/h)
            step = 0.001  # ~100m per update
            factor = step / distance
            new_x = current.x + dx * factor
            new_y = current.y + dy * factor
            
            vehicle.current_position = Point(new_x, new_y, srid=4326)
            vehicle.status = 'en_route'
            vehicle.speed_kmh = random.uniform(50, 70)
            vehicle.heading = (90 - (180 / 3.14159) * (dy / dx if dx != 0 else 0)) % 360
            
            incident.status = 'en_route'
            incident.save()

        vehicle.save()

    def move_towards_base(self, vehicle):
        """Move vehicle back to base facility."""
        current = vehicle.current_position
        target = vehicle.base_facility.location

        dx = target.x - current.x
        dy = target.y - current.y
        distance = (dx**2 + dy**2) ** 0.5

        # If close enough, mark as available
        if distance < 0.001:
            vehicle.current_position = target
            vehicle.status = 'available'
            vehicle.speed_kmh = 0
            self.stdout.write(f'{vehicle.callsign} returned to base')
        else:
            # Move towards base
            step = 0.001
            factor = step / distance
            new_x = current.x + dx * factor
            new_y = current.y + dy * factor
            
            vehicle.current_position = Point(new_x, new_y, srid=4326)
            vehicle.speed_kmh = random.uniform(40, 60)
            vehicle.heading = (90 - (180 / 3.14159) * (dy / dx if dx != 0 else 0)) % 360

        vehicle.save()

    def random_patrol(self, vehicle):
        """Simulate random patrol movement."""
        current = vehicle.current_position
        
        # Small random movement
        new_x = current.x + random.uniform(-0.0005, 0.0005)
        new_y = current.y + random.uniform(-0.0005, 0.0005)
        
        vehicle.current_position = Point(new_x, new_y, srid=4326)
        vehicle.speed_kmh = random.uniform(20, 40)
        vehicle.heading = random.uniform(0, 360)
        vehicle.save()
