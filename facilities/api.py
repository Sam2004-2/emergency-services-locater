"""
REST API endpoints for emergency facilities and county boundaries.

Provides GeoJSON-based RESTful API with spatial query capabilities including:
- Standard CRUD operations
- Within-radius queries
- K-nearest neighbor queries
- County containment queries
- Custom polygon queries
"""
from typing import Optional

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import GEOSGeometry, Point
from django.db.models import QuerySet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import County, EmergencyFacility
from .permissions import IsEditorOrReadOnly
from .serializers import CountyGeoSerializer, FacilityGeoSerializer
from .validators import parse_positive_meters, validate_lat_lon


# Constants
DEFAULT_NEAREST_LIMIT = 5
MAX_NEAREST_LIMIT = 50
DEFAULT_COVERAGE_RADIUS_M = 10000
MAX_COVERAGE_RADIUS_M = 100000


class CountyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API endpoint for county boundaries.
    
    Provides GeoJSON responses for Irish county administrative boundaries.
    Supports filtering by ISO code and English name.
    
    Example:
        GET /api/counties/
        GET /api/counties/?name_en=Dublin
        GET /api/counties/?iso_code=IE-D
    """
    
    queryset = County.objects.all().order_by('name_en')
    serializer_class = CountyGeoSerializer
    filterset_fields = ['iso_code', 'name_en']


class FacilityViewSet(viewsets.ModelViewSet):
    """
    RESTful API endpoints for emergency facilities with spatial query support.
    
    Standard CRUD operations plus custom spatial query actions:
    - within-radius: Find facilities within a specified radius from a point
    - nearest: Find K-nearest facilities from a point
    - within-county: Find facilities within a specific county
    - within-polygon: Find facilities within a custom polygon
    - coverage-buffers: Find facilities with distance metadata
    """

    queryset = EmergencyFacility.objects.all()
    serializer_class = FacilityGeoSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['type']
    ordering_fields = ['name', 'updated_at']
    
    def get_permissions(self):
        """
        Return appropriate permissions based on action.
        
        - Read operations (list, retrieve, spatial queries): Allow any
        - Write operations (create, update, delete): Require Editor role
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsEditorOrReadOnly()]
        return [AllowAny()]

    def _filtered_queryset(self) -> QuerySet:
        """
        Apply DRF filter backends to support ?type= query param for custom actions.
        
        Returns:
            Filtered queryset based on request parameters
        """
        return self.filter_queryset(self.get_queryset())

    @action(detail=False, methods=['get'], url_path='within-radius')
    def within_radius(self, request: Request) -> Response:
        """
        Find facilities within a specified radius from a point.
        
        Query Parameters:
            lat: Latitude of center point
            lon: Longitude of center point
            radius_m: Radius in meters
            type (optional): Filter by facility type
            
        Returns:
            GeoJSON FeatureCollection of facilities within radius, ordered by distance
        """
        lat, lon = validate_lat_lon(
            request.query_params.get('lat'),
            request.query_params.get('lon'),
        )
        radius_m = parse_positive_meters(request.query_params.get('radius_m'))
        point = Point(float(lon), float(lat), srid=4326)
        qs = (
            self._filtered_queryset()
            .filter(geom__distance_lte=(point, radius_m))
            .annotate(distance=Distance('geom', point))
            .order_by('distance')
        )
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page or qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='nearest')
    def nearest(self, request: Request) -> Response:
        """
        Find K-nearest facilities from a point.
        
        Query Parameters:
            lat: Latitude of center point
            lon: Longitude of center point
            limit (optional): Number of facilities to return (1-50, default 5)
            type (optional): Filter by facility type
            
        Returns:
            GeoJSON FeatureCollection of nearest facilities, ordered by distance
        """
        lat, lon = validate_lat_lon(
            request.query_params.get('lat'),
            request.query_params.get('lon'),
        )
        try:
            limit = int(request.query_params.get('limit', DEFAULT_NEAREST_LIMIT))
        except ValueError:
            return Response(
                {'detail': 'Limit must be an integer.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        limit = max(1, min(limit, MAX_NEAREST_LIMIT))
        point = Point(float(lon), float(lat), srid=4326)
        qs = (
            self._filtered_queryset()
            .annotate(distance=Distance('geom', point))
            .order_by('distance')[:limit]
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='within-county')
    def within_county(self, request: Request) -> Response:
        """
        Find facilities within a specific county.
        
        Query Parameters:
            id: County ID
            name: County name (case-insensitive)
            type (optional): Filter by facility type
            
        Note: Provide either 'id' or 'name', not both
            
        Returns:
            GeoJSON FeatureCollection of facilities within the county
        """
        county_id = request.query_params.get('id')
        county_name = request.query_params.get('name')

        county: Optional[County] = None
        if county_id:
            try:
                county = County.objects.get(pk=int(county_id))
            except (County.DoesNotExist, ValueError):
                return Response({'detail': 'County not found.'}, status=status.HTTP_404_NOT_FOUND)
        elif county_name:
            county = County.objects.filter(name_en__iexact=county_name).first()
            if not county:
                return Response({'detail': 'County not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'detail': 'Provide county id or name parameter.'}, status=status.HTTP_400_BAD_REQUEST)

        qs = self._filtered_queryset().filter(geom__within=county.geom)
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page or qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='within-polygon', permission_classes=[AllowAny])
    def within_polygon(self, request: Request) -> Response:
        """
        Find facilities within a custom polygon.
        
        Request Body:
            geometry: GeoJSON geometry object
            geom: WKT geometry string (alternative to geometry)
            type (optional): Override facility type filter
            
        Returns:
            GeoJSON FeatureCollection of facilities within the polygon
        """
        geom_payload = request.data.get('geometry') or request.data.get('geom')
        if not geom_payload:
            return Response(
                {'detail': "Provide GeoJSON in 'geometry' or WKT in 'geom'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            if isinstance(geom_payload, str):
                polygon = GEOSGeometry(geom_payload, srid=4326)
            else:
                polygon = GEOSGeometry(str(geom_payload), srid=4326)
        except Exception:
            return Response({'detail': 'Invalid geometry.'}, status=status.HTTP_400_BAD_REQUEST)

        if polygon.geom_type not in ('Polygon', 'MultiPolygon'):
            return Response(
                {'detail': 'Geometry must be Polygon or MultiPolygon.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = self._filtered_queryset()
        type_override = request.data.get('type')
        if type_override:
            qs = qs.filter(type=type_override)
        qs = qs.filter(geom__within=polygon)
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page or qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='coverage-buffers')
    def coverage_buffers(self, request: Request) -> Response:
        """
        Find facilities within radius with distance metadata.
        
        Query Parameters:
            lat: Latitude of center point
            lon: Longitude of center point
            radius_m (optional): Radius in meters (default 10km, max 100km)
            type (optional): Filter by facility type
            
        Returns:
            JSON object with radius_m and results array of facilities with distances
        """
        lat, lon = validate_lat_lon(
            request.query_params.get('lat'),
            request.query_params.get('lon'),
        )
        radius_m = parse_positive_meters(
            request.query_params.get('radius_m'),
            default=DEFAULT_COVERAGE_RADIUS_M,
            maxv=MAX_COVERAGE_RADIUS_M,
        )
        point = Point(float(lon), float(lat), srid=4326)
        qs = (
            self._filtered_queryset()
            .filter(geom__distance_lte=(point, radius_m))
            .annotate(distance=Distance('geom', point))
            .order_by('distance')
        )
        serializer = self.get_serializer(qs, many=True)
        return Response({'radius_m': radius_m, 'results': serializer.data})
