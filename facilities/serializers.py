"""
GeoJSON serializers for county boundaries and emergency facilities.

Uses Django REST Framework GIS to convert model instances to GeoJSON format
following the GeoJSON specification (RFC 7946).
"""
from rest_framework_gis.fields import GeometryField
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import County, EmergencyFacility


class CountyGeoSerializer(GeoFeatureModelSerializer):
    """
    GeoJSON serializer for county boundaries.
    
    Converts County model instances to GeoJSON format with multilingual
    names and ISO codes as properties.
    """
    
    geom = GeometryField()
    
    class Meta:
        model = County
        geo_field = 'geom'
        fields = ('id', 'name_en', 'name_local', 'iso_code')


class FacilityGeoSerializer(GeoFeatureModelSerializer):
    """
    GeoJSON serializer for emergency facilities.
    
    Converts EmergencyFacility model instances to GeoJSON format
    with properties and geometry following the GeoJSON specification.
    """
    
    geom = GeometryField()
    
    class Meta:
        model = EmergencyFacility
        geo_field = 'geom'
        fields = (
            'id',
            'name',
            'type',
            'address',
            'phone',
            'website',
            'properties',
            'created_at',
            'updated_at',
        )
