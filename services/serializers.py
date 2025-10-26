from rest_framework_gis.fields import GeometryField
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import EmergencyFacility


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
