from rest_framework import viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from .models import County
from .serializers import CountyGeoSerializer


class CountyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API endpoint for county boundaries.
    
    Provides GeoJSON responses for Irish county administrative boundaries.
    Supports filtering by ISO code and English name.
    
    Example:
        GET /api/boundaries/counties/
        GET /api/boundaries/counties/?name_en=Dublin
        GET /api/boundaries/counties/?iso_code=IE-D
    """
    
    queryset = County.objects.all().order_by('name_en')
    serializer_class = CountyGeoSerializer
    filterset_fields = ['iso_code', 'name_en']
