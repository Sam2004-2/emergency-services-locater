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
    """
    
    name = models.CharField(max_length=200, help_text="Facility name")
    type = models.CharField(max_length=32, choices=FACILITY_CHOICES, db_index=True)
    address = models.CharField(max_length=500, null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    website = models.URLField(max_length=500, null=True, blank=True)
    properties = models.JSONField(default=dict, blank=True, help_text="Additional metadata")
    geom = models.PointField(srid=4326, spatial_index=True, help_text="Facility location (WGS84)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = EmergencyFacilityQuerySet.as_manager()

    class Meta:
        db_table = 'services_emergencyfacility'
        verbose_name = 'Emergency Facility'
        verbose_name_plural = 'Emergency Facilities'
        ordering = ['name']
        indexes = [
            models.Index(fields=['type', 'created_at']),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.type})"
