from rest_framework_gis.fields import GeometryField
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import County


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
