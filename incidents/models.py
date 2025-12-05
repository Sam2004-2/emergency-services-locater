"""
Models for incident management and emergency dispatch.

Contains models for tracking incidents, vehicles/units, assignments,
and dispatcher operations with PostGIS spatial support.
"""
import uuid
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.utils import timezone


# Incident type choices
INCIDENT_TYPE_CHOICES = (
    ('fire', 'Fire'),
    ('medical', 'Medical Emergency'),
    ('police', 'Police'),
    ('traffic', 'Traffic Accident'),
    ('multi_agency', 'Multi-Agency'),
    ('hazmat', 'Hazardous Materials'),
    ('rescue', 'Search & Rescue'),
    ('other', 'Other'),
)

# Incident priority choices
INCIDENT_PRIORITY_CHOICES = (
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('critical', 'Critical'),
)

# Incident status choices
INCIDENT_STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('dispatched', 'Dispatched'),
    ('en_route', 'En Route'),
    ('on_scene', 'On Scene'),
    ('resolved', 'Resolved'),
    ('cancelled', 'Cancelled'),
)

# Vehicle type choices
VEHICLE_TYPE_CHOICES = (
    ('ambulance', 'Ambulance'),
    ('fire_truck', 'Fire Truck'),
    ('police_car', 'Police Car'),
    ('rescue_unit', 'Rescue Unit'),
    ('hazmat_unit', 'Hazmat Unit'),
    ('command_vehicle', 'Command Vehicle'),
    ('helicopter', 'Helicopter'),
    ('boat', 'Rescue Boat'),
)

# Vehicle status choices
VEHICLE_STATUS_CHOICES = (
    ('available', 'Available'),
    ('dispatched', 'Dispatched'),
    ('en_route', 'En Route'),
    ('on_scene', 'On Scene'),
    ('returning', 'Returning'),
    ('out_of_service', 'Out of Service'),
    ('maintenance', 'Under Maintenance'),
)


class IncidentQuerySet(models.QuerySet):
    """Custom QuerySet with spatial query helpers for incidents."""

    def active(self):
        """Return only active (non-resolved, non-cancelled) incidents."""
        return self.exclude(status__in=['resolved', 'cancelled'])

    def pending(self):
        """Return pending incidents awaiting dispatch."""
        return self.filter(status='pending')

    def by_priority(self):
        """Order incidents by priority (critical first)."""
        priority_order = models.Case(
            models.When(priority='critical', then=0),
            models.When(priority='high', then=1),
            models.When(priority='medium', then=2),
            models.When(priority='low', then=3),
            default=4,
            output_field=models.IntegerField(),
        )
        return self.annotate(priority_order=priority_order).order_by('priority_order', '-reported_at')

    def within_radius(self, point: Point, meters: float):
        """Filter incidents within a specified radius from a point."""
        return self.filter(location__distance_lte=(point, meters))

    def nearest_to(self, point: Point, limit: int = 10):
        """Find nearest incidents to a point."""
        return self.annotate(distance=Distance('location', point)).order_by('distance')[:limit]


class Incident(models.Model):
    """
    Emergency incident with spatial location and lifecycle tracking.
    
    Represents an emergency event requiring dispatch of vehicles/units
    with full status tracking and assignment history.
    """
    
    # Unique identifier
    incident_number = models.CharField(
        max_length=20, 
        unique=True, 
        editable=False,
        help_text="Unique incident reference number"
    )
    
    # Incident classification
    incident_type = models.CharField(
        max_length=20, 
        choices=INCIDENT_TYPE_CHOICES, 
        db_index=True
    )
    priority = models.CharField(
        max_length=10, 
        choices=INCIDENT_PRIORITY_CHOICES, 
        default='medium',
        db_index=True
    )
    status = models.CharField(
        max_length=15, 
        choices=INCIDENT_STATUS_CHOICES, 
        default='pending',
        db_index=True
    )
    
    # Incident details
    title = models.CharField(max_length=200, help_text="Brief incident description")
    description = models.TextField(blank=True, help_text="Detailed incident description")
    
    # Location
    location = models.PointField(srid=4326, spatial_index=True, help_text="Incident location (WGS84)")
    address = models.CharField(max_length=500, blank=True, help_text="Address of incident")
    
    # Reporter information
    reporter_name = models.CharField(max_length=100, blank=True)
    reporter_phone = models.CharField(max_length=20, blank=True)
    
    # Timestamps
    reported_at = models.DateTimeField(default=timezone.now, db_index=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    arrived_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Relationships
    dispatcher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dispatched_incidents',
        help_text="Dispatcher who handled this incident"
    )
    
    # Additional metadata
    notes = models.TextField(blank=True, help_text="Internal notes")
    properties = models.JSONField(default=dict, blank=True, help_text="Additional metadata")
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = IncidentQuerySet.as_manager()
    
    class Meta:
        db_table = 'incidents_incident'
        verbose_name = 'Incident'
        verbose_name_plural = 'Incidents'
        ordering = ['-reported_at']
        indexes = [
            models.Index(fields=['status', 'priority', 'reported_at']),
            models.Index(fields=['incident_type', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.incident_number:
            self.incident_number = self._generate_incident_number()
        super().save(*args, **kwargs)
    
    def _generate_incident_number(self):
        """Generate a unique incident number: INC-YYYYMMDD-XXXX"""
        today = timezone.now().strftime('%Y%m%d')
        prefix = f"INC-{today}-"
        
        # Get the last incident number for today
        last_incident = (
            Incident.objects
            .filter(incident_number__startswith=prefix)
            .order_by('-incident_number')
            .first()
        )
        
        if last_incident:
            last_num = int(last_incident.incident_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f"{prefix}{new_num:04d}"
    
    def __str__(self) -> str:
        return f"{self.incident_number} - {self.title}"
    
    @property
    def is_active(self) -> bool:
        """Check if incident is still active."""
        return self.status not in ['resolved', 'cancelled']
    
    @property
    def response_time(self):
        """Calculate response time (dispatch to arrival)."""
        if self.dispatched_at and self.arrived_at:
            return self.arrived_at - self.dispatched_at
        return None
    
    @property
    def resolution_time(self):
        """Calculate total resolution time."""
        if self.reported_at and self.resolved_at:
            return self.resolved_at - self.reported_at
        return None
    
    def assign_vehicle(self, vehicle, dispatcher=None):
        """Assign a vehicle to this incident."""
        assignment = VehicleAssignment.objects.create(
            incident=self,
            vehicle=vehicle,
            assigned_by=dispatcher
        )
        
        # Update vehicle status
        vehicle.status = 'dispatched'
        vehicle.current_incident = self
        vehicle.save()
        
        # Update incident status if pending
        if self.status == 'pending':
            self.status = 'dispatched'
            self.dispatched_at = timezone.now()
            self.dispatcher = dispatcher
            self.save()
        
        return assignment


class VehicleQuerySet(models.QuerySet):
    """Custom QuerySet with spatial query helpers for vehicles."""

    def available(self):
        """Return only available vehicles."""
        return self.filter(status='available')

    def active(self):
        """Return vehicles that are on duty (not out of service/maintenance)."""
        return self.exclude(status__in=['out_of_service', 'maintenance'])

    def by_type(self, vehicle_type):
        """Filter vehicles by type."""
        return self.filter(vehicle_type=vehicle_type)

    def nearest_available(self, point: Point, vehicle_type: str = None, limit: int = 5):
        """Find nearest available vehicles to a point."""
        qs = self.available()
        if vehicle_type:
            qs = qs.filter(vehicle_type=vehicle_type)
        return qs.annotate(distance=Distance('current_location', point)).order_by('distance')[:limit]


class Vehicle(models.Model):
    """
    Emergency response vehicle/unit with real-time location tracking.
    
    Represents ambulances, fire trucks, police cars, and other emergency
    response units with status and location tracking.
    """
    
    # Identification
    call_sign = models.CharField(
        max_length=20, 
        unique=True,
        help_text="Radio call sign (e.g., AMB-01, FIRE-03)"
    )
    vehicle_type = models.CharField(
        max_length=20, 
        choices=VEHICLE_TYPE_CHOICES,
        db_index=True
    )
    status = models.CharField(
        max_length=15, 
        choices=VEHICLE_STATUS_CHOICES, 
        default='available',
        db_index=True
    )
    
    # Vehicle details
    registration = models.CharField(max_length=20, blank=True, help_text="Vehicle registration number")
    make_model = models.CharField(max_length=100, blank=True, help_text="Vehicle make and model")
    capacity = models.PositiveIntegerField(default=2, help_text="Crew capacity")
    
    # Equipment and capabilities
    equipment = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of equipment on vehicle"
    )
    capabilities = models.JSONField(
        default=list, 
        blank=True,
        help_text="Special capabilities (e.g., ALS, hazmat)"
    )
    
    # Location tracking
    current_location = models.PointField(
        srid=4326, 
        spatial_index=True,
        null=True,
        blank=True,
        help_text="Current vehicle location (WGS84)"
    )
    location_updated_at = models.DateTimeField(null=True, blank=True)
    
    # Home station (for returning)
    home_station = models.ForeignKey(
        'facilities.EmergencyFacility',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vehicles',
        help_text="Home station/facility"
    )
    
    # Current assignment
    current_incident = models.ForeignKey(
        Incident,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_vehicles',
        help_text="Currently assigned incident"
    )
    
    # Additional metadata
    notes = models.TextField(blank=True)
    properties = models.JSONField(default=dict, blank=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = VehicleQuerySet.as_manager()
    
    class Meta:
        db_table = 'incidents_vehicle'
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'
        ordering = ['call_sign']
        indexes = [
            models.Index(fields=['vehicle_type', 'status']),
        ]
    
    def __str__(self) -> str:
        return f"{self.call_sign} ({self.get_vehicle_type_display()})"
    
    @property
    def is_available(self) -> bool:
        """Check if vehicle is available for dispatch."""
        return self.status == 'available'
    
    def update_location(self, lat: float, lon: float):
        """Update vehicle's current location."""
        self.current_location = Point(lon, lat, srid=4326)
        self.location_updated_at = timezone.now()
        self.save(update_fields=['current_location', 'location_updated_at', 'updated_at'])
    
    def set_available(self):
        """Mark vehicle as available and clear current incident."""
        self.status = 'available'
        self.current_incident = None
        self.save()
    
    def set_out_of_service(self, reason: str = None):
        """Mark vehicle as out of service."""
        self.status = 'out_of_service'
        if reason:
            self.notes = f"Out of service: {reason}\n{self.notes}"
        self.save()


class VehicleAssignment(models.Model):
    """
    Assignment linking a vehicle to an incident.
    
    Tracks the assignment lifecycle including dispatch time, arrival,
    and completion with optional route information.
    """
    
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    
    # Assignment tracking
    assigned_at = models.DateTimeField(default=timezone.now)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    en_route_at = models.DateTimeField(null=True, blank=True)
    arrived_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Assignment metadata
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vehicle_assignments'
    )
    
    # Route information
    route_geometry = models.JSONField(
        null=True, 
        blank=True,
        help_text="GeoJSON LineString of calculated route"
    )
    route_distance_m = models.FloatField(null=True, blank=True, help_text="Route distance in meters")
    route_duration_s = models.FloatField(null=True, blank=True, help_text="Estimated route duration in seconds")
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'incidents_vehicleassignment'
        verbose_name = 'Vehicle Assignment'
        verbose_name_plural = 'Vehicle Assignments'
        ordering = ['-assigned_at']
        unique_together = [['incident', 'vehicle', 'assigned_at']]
    
    def __str__(self) -> str:
        return f"{self.vehicle.call_sign} → {self.incident.incident_number}"
    
    @property
    def response_time(self):
        """Calculate response time (dispatch to arrival)."""
        if self.dispatched_at and self.arrived_at:
            return self.arrived_at - self.dispatched_at
        return None
    
    def mark_en_route(self):
        """Mark vehicle as en route to incident."""
        self.en_route_at = timezone.now()
        self.vehicle.status = 'en_route'
        self.vehicle.save()
        self.save()
    
    def mark_arrived(self):
        """Mark vehicle as arrived at incident."""
        self.arrived_at = timezone.now()
        self.vehicle.status = 'on_scene'
        self.vehicle.save()
        
        # Update incident if this is first arrival
        if not self.incident.arrived_at:
            self.incident.arrived_at = self.arrived_at
            self.incident.status = 'on_scene'
            self.incident.save()
        
        self.save()
    
    def mark_completed(self):
        """Mark assignment as completed."""
        self.completed_at = timezone.now()
        self.vehicle.status = 'returning'
        self.vehicle.current_incident = None
        self.vehicle.save()
        self.save()


class DispatcherProfile(models.Model):
    """
    Extended profile for dispatcher users.
    
    Tracks dispatcher-specific information like shift details
    and active incident assignments.
    """
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dispatcher_profile'
    )
    
    # Dispatcher details
    badge_number = models.CharField(max_length=20, blank=True)
    is_on_duty = models.BooleanField(default=False)
    shift_start = models.DateTimeField(null=True, blank=True)
    shift_end = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    incidents_handled = models.PositiveIntegerField(default=0)
    
    # Settings
    notification_preferences = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'incidents_dispatcherprofile'
        verbose_name = 'Dispatcher Profile'
        verbose_name_plural = 'Dispatcher Profiles'
    
    def __str__(self) -> str:
        return f"Dispatcher: {self.user.username}"
    
    def start_shift(self):
        """Start dispatcher shift."""
        self.is_on_duty = True
        self.shift_start = timezone.now()
        self.shift_end = None
        self.save()
    
    def end_shift(self):
        """End dispatcher shift."""
        self.is_on_duty = False
        self.shift_end = timezone.now()
        self.save()
