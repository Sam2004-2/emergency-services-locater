from django.contrib.gis.db import models
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db.models import QuerySet


FACILITY_CHOICES = (
    ('hospital', 'Hospital'),
    ('fire_station', 'Fire Station'),
    ('police_station', 'Police Station'),
    ('ambulance_base', 'Ambulance Base'),
)


class EmergencyFacilityQuerySet(models.QuerySet):
    """Custom QuerySet with spatial query helpers for emergency facilities."""

    def within_radius(self, point: Point, meters: float) -> QuerySet:
        """
        Filter facilities within a specified radius from a point.
        
        Args:
            point: Center point (GEOS Point with SRID 4326)
            meters: Radius in meters
            
        Returns:
            QuerySet of facilities within the radius
        """
        return self.filter(geom__distance_lte=(point, meters))

    def knn_nearest(self, point: Point, limit: int = 5) -> QuerySet:
        """
        Find K-nearest facilities from a point.
        
        Args:
            point: Center point (GEOS Point with SRID 4326)
            limit: Number of facilities to return
            
        Returns:
            QuerySet ordered by distance with distance annotation
        """
        return self.annotate(distance=Distance('geom', point)).order_by('distance')[:limit]


class EmergencyFacility(models.Model):
    """
    Emergency service facility with spatial location.
    
    Represents various emergency service locations (hospitals, fire stations,
    police stations, ambulance bases) with geographic coordinates for spatial queries.
    
    Note: This model uses managed=False as data is maintained externally.
    """
    
    id = models.IntegerField(primary_key=True)
    name = models.TextField()
    type = models.CharField(max_length=32, choices=FACILITY_CHOICES)
    address = models.TextField(null=True, blank=True)
    phone = models.TextField(null=True, blank=True)
    website = models.TextField(null=True, blank=True)
    properties = models.JSONField(default=dict, blank=True)
    geom = models.PointField(srid=4326, help_text="Facility location (WGS84)")
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    objects = EmergencyFacilityQuerySet.as_manager()

    class Meta:
        db_table = 'emergency_facility'
        managed = False
        verbose_name = 'Emergency Facility'
        verbose_name_plural = 'Emergency Facilities'

    def __str__(self) -> str:
        return f"{self.name} ({self.type})"
