"""
Incident management models with spatial support.

Provides models for emergency incidents, response vehicles, and dispatch
records with PostGIS integration for location-based operations.
"""
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.utils import timezone


INCIDENT_TYPE_CHOICES = (
    ('fire', 'Fire'),
    ('medical', 'Medical Emergency'),
    ('crime', 'Crime/Police'),
    ('accident', 'Traffic Accident'),
)

INCIDENT_SEVERITY_CHOICES = (
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('critical', 'Critical'),
)

INCIDENT_STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('dispatched', 'Dispatched'),
    ('en_route', 'En Route'),
    ('on_scene', 'On Scene'),
    ('resolved', 'Resolved'),
    ('cancelled', 'Cancelled'),
)

VEHICLE_TYPE_CHOICES = (
    ('ambulance', 'Ambulance'),
    ('fire_engine', 'Fire Engine'),
    ('police_car', 'Police Car'),
    ('helicopter', 'Helicopter'),
)

VEHICLE_STATUS_CHOICES = (
    ('available', 'Available'),
    ('dispatched', 'Dispatched'),
    ('en_route', 'En Route'),
    ('on_scene', 'On Scene'),
    ('returning', 'Returning to Base'),
    ('maintenance', 'Under Maintenance'),
)


class IncidentQuerySet(models.QuerySet):
    """Custom QuerySet with spatial query helpers for incidents."""

    def active(self):
        """Return incidents that are not resolved or cancelled."""
        return self.exclude(status__in=['resolved', 'cancelled'])

    def within_radius(self, point: Point, meters: float):
        """Filter incidents within a specified radius from a point."""
        return self.filter(location__distance_lte=(point, meters))

    def nearest(self, point: Point, limit: int = 5):
        """Find K-nearest incidents from a point."""
        return self.annotate(
            distance=Distance('location', point)
        ).order_by('distance')[:limit]


class Incident(models.Model):
    """
    Emergency incident with spatial location and lifecycle tracking.

    Represents an emergency event that requires response from emergency
    services, with location, type, severity, and status tracking.
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    incident_type = models.CharField(
        max_length=20,
        choices=INCIDENT_TYPE_CHOICES,
        db_index=True
    )
    severity = models.CharField(
        max_length=10,
        choices=INCIDENT_SEVERITY_CHOICES,
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=INCIDENT_STATUS_CHOICES,
        default='pending',
        db_index=True
    )

    # Spatial location
    location = models.PointField(srid=4326, spatial_index=True)
    address = models.CharField(max_length=500, blank=True)

    # Relationships
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reported_incidents'
    )
    assigned_responder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_incidents'
    )
    nearest_facility = models.ForeignKey(
        'services.EmergencyFacility',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='nearby_incidents'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    # Cached route data (from OSRM)
    route_geometry = models.LineStringField(srid=4326, null=True, blank=True)
    route_distance_m = models.FloatField(null=True, blank=True)
    route_duration_s = models.FloatField(null=True, blank=True)

    objects = IncidentQuerySet.as_manager()

    class Meta:
        db_table = 'incidents_incident'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'severity']),
            models.Index(fields=['incident_type', 'status']),
        ]

    def __str__(self):
        return f"{self.get_incident_type_display()} - {self.title} ({self.status})"

    def dispatch(self, responder, vehicle=None):
        """Dispatch this incident to a responder with optional vehicle."""
        self.assigned_responder = responder
        self.status = 'dispatched'
        self.dispatched_at = timezone.now()
        self.save()

    def resolve(self):
        """Mark this incident as resolved."""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.save()

    @property
    def is_active(self):
        """Check if incident is still active (not resolved/cancelled)."""
        return self.status not in ['resolved', 'cancelled']


class VehicleQuerySet(models.QuerySet):
    """Custom QuerySet for vehicle queries."""

    def available(self):
        """Return only available vehicles."""
        return self.filter(status='available')

    def by_type(self, vehicle_type):
        """Filter vehicles by type."""
        return self.filter(vehicle_type=vehicle_type)

    def nearest_available(self, point: Point, vehicle_type=None, limit: int = 5):
        """Find nearest available vehicles to a point."""
        qs = self.available()
        if vehicle_type:
            qs = qs.by_type(vehicle_type)
        return qs.annotate(
            distance=Distance('current_position', point)
        ).order_by('distance')[:limit]


class Vehicle(models.Model):
    """
    Emergency response vehicle with real-time position tracking.

    Represents a vehicle that can be dispatched to incidents,
    with current position and status tracking.
    """
    callsign = models.CharField(max_length=50, unique=True)
    vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_TYPE_CHOICES,
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=VEHICLE_STATUS_CHOICES,
        default='available',
        db_index=True
    )

    # Current position
    current_position = models.PointField(srid=4326, spatial_index=True)
    heading = models.FloatField(default=0, help_text="Heading in degrees (0-360)")
    speed_kmh = models.FloatField(default=0)

    # Base facility
    base_facility = models.ForeignKey(
        'services.EmergencyFacility',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vehicles'
    )

    # Current assignment
    current_incident = models.ForeignKey(
        'Incident',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_vehicles'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_position_update = models.DateTimeField(auto_now=True)

    objects = VehicleQuerySet.as_manager()

    class Meta:
        db_table = 'incidents_vehicle'
        ordering = ['callsign']

    def __str__(self):
        return f"{self.callsign} ({self.get_vehicle_type_display()})"

    @property
    def is_available(self):
        """Check if vehicle is available for dispatch."""
        return self.status == 'available'


class Dispatch(models.Model):
    """
    Dispatch record linking incident, vehicle, and responder.

    Maintains an audit trail of all dispatch actions with route
    information and timestamps for each stage.
    """
    incident = models.ForeignKey(
        'Incident',
        on_delete=models.CASCADE,
        related_name='dispatches'
    )
    vehicle = models.ForeignKey(
        'Vehicle',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dispatches'
    )
    responder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='dispatch_assignments'
    )
    dispatcher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_dispatches'
    )

    # Route information
    origin = models.PointField(srid=4326)
    destination = models.PointField(srid=4326)
    route_geometry = models.LineStringField(srid=4326, null=True, blank=True)
    route_distance_m = models.FloatField(null=True, blank=True)
    route_duration_s = models.FloatField(null=True, blank=True)

    # Status timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    arrived_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'incidents_dispatch'
        ordering = ['-created_at']
        verbose_name_plural = 'Dispatches'

    def __str__(self):
        return f"Dispatch #{self.id} - {self.incident}"

    def acknowledge(self):
        """Mark dispatch as acknowledged by responder."""
        self.acknowledged_at = timezone.now()
        self.save()
        if self.vehicle:
            self.vehicle.status = 'en_route'
            self.vehicle.save()
        self.incident.status = 'en_route'
        self.incident.save()

    def arrive(self):
        """Mark arrival at incident scene."""
        self.arrived_at = timezone.now()
        self.save()
        if self.vehicle:
            self.vehicle.status = 'on_scene'
            self.vehicle.save()
        self.incident.status = 'on_scene'
        self.incident.save()

    def complete(self):
        """Mark dispatch as completed."""
        self.completed_at = timezone.now()
        self.save()
        if self.vehicle:
            self.vehicle.status = 'returning'
            self.vehicle.current_incident = None
            self.vehicle.save()
