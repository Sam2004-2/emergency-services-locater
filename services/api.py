from typing import Optional, Tuple

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import GEOSGeometry, Point
from django.db.models import QuerySet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from boundaries.models import County
from core.utils.validators import parse_positive_meters, validate_lat_lon

from .models import EmergencyFacility
from .serializers import FacilityGeoSerializer

DEFAULT_NEAREST_LIMIT = 5
MAX_NEAREST_LIMIT = 50
DEFAULT_COVERAGE_RADIUS_M = 10000
MAX_COVERAGE_RADIUS_M = 100000


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
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['type']
    ordering_fields = ['name', 'updated_at']

    def _filtered_queryset(self) -> QuerySet[EmergencyFacility]:
        """Apply DRF filter backends to support ?type= query param for custom actions."""
        return self.filter_queryset(self.get_queryset())

    def _create_point_from_request(self, request: Request) -> Point:
        """Create a Point from lat/lon query parameters."""
        lat, lon = validate_lat_lon(
            request.query_params.get('lat'),
            request.query_params.get('lon'),
        )
        return Point(float(lon), float(lat), srid=4326)

    def _get_county_from_request(self, request: Request) -> Tuple[Optional[County], Optional[Response]]:
        """
        Get county from request parameters (id or name).
        
        Returns:
            Tuple of (county, error_response). If error_response is not None, return it.
        """
        county_id = request.query_params.get('id')
        county_name = request.query_params.get('name')

        if county_id:
            try:
                county = County.objects.get(pk=int(county_id))
                return county, None
            except (County.DoesNotExist, ValueError):
                return None, Response({'detail': 'County not found.'}, status=status.HTTP_404_NOT_FOUND)
        elif county_name:
            county = County.objects.filter(name_en__iexact=county_name).first()
            if not county:
                return None, Response({'detail': 'County not found.'}, status=status.HTTP_404_NOT_FOUND)
            return county, None
        else:
            return None, Response(
                {'detail': 'Provide county id or name parameter.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def _paginated_response(self, queryset: QuerySet[EmergencyFacility]) -> Response:
        """Return paginated or unpaginated response for a queryset."""
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page or queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='within-radius')
    def within_radius(self, request: Request) -> Response:
        """
        Find facilities within a specified radius from a point.
        
        Query Parameters:
            lat: Latitude of center point
            lon: Longitude of center point
            radius_m: Radius in meters
            type (optional): Filter by facility type
        """
        point = self._create_point_from_request(request)
        radius_m = parse_positive_meters(request.query_params.get('radius_m'))
        qs = (
            self._filtered_queryset()
            .filter(geom__distance_lte=(point, radius_m))
            .annotate(distance=Distance('geom', point))
            .order_by('distance')
        )
        return self._paginated_response(qs)

    @action(detail=False, methods=['get'], url_path='nearest')
    def nearest(self, request: Request) -> Response:
        """
        Find K-nearest facilities from a point.
        
        Query Parameters:
            lat: Latitude of center point
            lon: Longitude of center point
            limit (optional): Number of facilities to return (1-50, default 5)
            type (optional): Filter by facility type
        """
        point = self._create_point_from_request(request)
        try:
            limit = int(request.query_params.get('limit', DEFAULT_NEAREST_LIMIT))
        except ValueError:
            return Response(
                {'detail': 'Limit must be an integer.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        limit = max(1, min(limit, MAX_NEAREST_LIMIT))
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
        """
        county, error_response = self._get_county_from_request(request)
        if error_response:
            return error_response

        qs = self._filtered_queryset().filter(geom__within=county.geom)
        return self._paginated_response(qs)

    @action(detail=False, methods=['post'], url_path='within-polygon', permission_classes=[AllowAny])
    def within_polygon(self, request: Request) -> Response:
        """
        Find facilities within a custom polygon.
        
        Request Body:
            geometry: GeoJSON geometry object
            geom: WKT geometry string (alternative to geometry)
            type (optional): Override facility type filter
        """
        geom_payload = request.data.get('geometry') or request.data.get('geom')
        if not geom_payload:
            return Response(
                {'detail': "Provide GeoJSON in 'geometry' or WKT in 'geom'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            polygon = GEOSGeometry(
                geom_payload if isinstance(geom_payload, str) else str(geom_payload),
                srid=4326
            )
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
        return self._paginated_response(qs)

    @action(detail=False, methods=['get'], url_path='coverage-buffers')
    def coverage_buffers(self, request: Request) -> Response:
        """
        Find facilities within radius with distance metadata.
        
        Query Parameters:
            lat: Latitude of center point
            lon: Longitude of center point
            radius_m (optional): Radius in meters (default 10km, max 100km)
            type (optional): Filter by facility type
        """
        point = self._create_point_from_request(request)
        radius_m = parse_positive_meters(
            request.query_params.get('radius_m'),
            default=DEFAULT_COVERAGE_RADIUS_M,
            maxv=MAX_COVERAGE_RADIUS_M,
        )
        qs = (
            self._filtered_queryset()
            .filter(geom__distance_lte=(point, radius_m))
            .annotate(distance=Distance('geom', point))
            .order_by('distance')
        )
        serializer = self.get_serializer(qs, many=True)
        return Response({'radius_m': radius_m, 'results': serializer.data})
