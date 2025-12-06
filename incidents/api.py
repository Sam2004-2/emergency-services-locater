"""
REST API views for incident management.

Provides ViewSets for incidents, vehicles, and dispatches with
role-based permissions and custom actions for dispatch and routing.
"""
from django.contrib.gis.geos import Point
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsDispatcher, IsDispatcherOrReadOnly
from services.models import EmergencyFacility

from .models import Dispatch, Incident, Vehicle
from .routing import OSRMService
from .serializers import (
    DispatchSerializer,
    IncidentListSerializer,
    IncidentSerializer,
    VehicleSerializer,
)


class IncidentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing emergency incidents.

    Provides CRUD operations plus custom actions for dispatch,
    status updates, and routing.
    """
    permission_classes = [IsAuthenticated, IsDispatcherOrReadOnly]
    pagination_class = None  # Disable pagination to preserve GeoJSON FeatureCollection structure
    # filter_backends = [DjangoFilterBackend]
    # filterset_fields = ['status', 'incident_type', 'severity']

    def get_queryset(self):
        """Return incidents with spatial annotations."""
        queryset = Incident.objects.select_related(
            'reported_by',
            'assigned_responder',
            'nearest_facility'
        ).all()
        
        # Manual filtering to avoid django-filter issues
        if hasattr(self.request, 'query_params'):
            params = self.request.query_params
        else:
            params = self.request.GET
            
        if 'status' in params:
            queryset = queryset.filter(status=params['status'])
        if 'incident_type' in params:
            queryset = queryset.filter(incident_type=params['incident_type'])
        if 'severity' in params:
            queryset = queryset.filter(severity=params['severity'])
            
        return queryset

    def get_serializer_class(self):
        """Use lightweight serializer for list views."""
        if getattr(self, 'action', None) == 'list':
            return IncidentListSerializer
        return IncidentSerializer

    def perform_create(self, serializer):
        """Set reporter to current user and find nearest facility."""
        incident = serializer.save(reported_by=self.request.user)

        # Find nearest facility based on incident type
        facility_type_map = {
            'fire': 'fire_station',
            'medical': 'hospital',
            'crime': 'police_station',
            'accident': 'hospital'
        }
        facility_type = facility_type_map.get(incident.incident_type)

        if facility_type:
            nearest = EmergencyFacility.objects.filter(
                facility_type=facility_type
            ).nearest(incident.location, limit=1).first()

            if nearest:
                incident.nearest_facility = nearest
                incident.save()

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Return all active (non-resolved) incidents."""
        queryset = self.get_queryset().active()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsDispatcher], url_path='dispatch', url_name='dispatch')
    def dispatch_vehicle(self, request, pk=None):
        """
        Dispatch a vehicle and responder to this incident.

        POST /api/incidents/{id}/dispatch/
        Body: {
            vehicle_id: int,
            responder_id: int (optional)
        }
        """
        incident = self.get_object()

        if incident.status not in ['pending', 'dispatched']:
            return Response(
                {'error': 'Incident is already being handled or resolved'},
                status=status.HTTP_400_BAD_REQUEST
            )

        vehicle_id = request.data.get('vehicle_id')
        responder_id = request.data.get('responder_id')

        if not vehicle_id:
            return Response(
                {'error': 'vehicle_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            vehicle = Vehicle.objects.get(id=vehicle_id)
        except Vehicle.DoesNotExist:
            return Response(
                {'error': 'Vehicle not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not vehicle.is_available:
            return Response(
                {'error': 'Vehicle is not available'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get route from vehicle to incident
        route_data = OSRMService.get_route(vehicle.current_position, incident.location)

        # Create dispatch record
        dispatch = Dispatch.objects.create(
            incident=incident,
            vehicle=vehicle,
            responder_id=responder_id,
            dispatcher=request.user,
            origin=vehicle.current_position,
            destination=incident.location,
            route_geometry=route_data['geometry'] if route_data else None,
            route_distance_m=route_data['distance'] if route_data else None,
            route_duration_s=route_data['duration'] if route_data else None
        )

        # Update incident
        incident.status = 'dispatched'
        incident.dispatched_at = timezone.now()
        if responder_id:
            incident.assigned_responder_id = responder_id
        if route_data:
            incident.route_geometry = route_data['geometry']
            incident.route_distance_m = route_data['distance']
            incident.route_duration_s = route_data['duration']
        incident.save()

        # Update vehicle
        vehicle.status = 'dispatched'
        vehicle.current_incident = incident
        vehicle.save()

        serializer = self.get_serializer(incident)
        return Response({
            'incident': serializer.data,
            'dispatch': DispatchSerializer(dispatch).data
        })

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Update incident status.

        POST /api/incidents/{id}/update-status/
        Body: {status: string}

        Allowed for assigned responder or dispatcher.
        """
        incident = self.get_object()
        new_status = request.data.get('status')

        if not new_status:
            return Response(
                {'error': 'status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check permissions
        user = request.user
        profile = getattr(user, 'profile', None)
        is_assigned = incident.assigned_responder == user
        is_dispatcher = profile and profile.is_dispatcher

        if not (is_assigned or is_dispatcher):
            return Response(
                {'error': 'Only assigned responder or dispatcher can update status'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Update status
        incident.status = new_status
        if new_status == 'resolved':
            incident.resolved_at = timezone.now()
        incident.save()

        serializer = self.get_serializer(incident)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def route(self, request, pk=None):
        """
        Get OSRM route to this incident.

        GET /api/incidents/{id}/route/?from_lat=x&from_lng=y
        """
        incident = self.get_object()

        from_lat = request.query_params.get('from_lat')
        from_lng = request.query_params.get('from_lng')

        if not (from_lat and from_lng):
            return Response(
                {'error': 'from_lat and from_lng are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            origin = Point(float(from_lng), float(from_lat), srid=4326)
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid coordinates'},
                status=status.HTTP_400_BAD_REQUEST
            )

        route_data = OSRMService.get_route(origin, incident.location)

        if not route_data:
            return Response(
                {'error': 'Could not calculate route'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            'geometry': {
                'type': 'LineString',
                'coordinates': list(route_data['geometry'].coords)
            },
            'distance': route_data['distance'],
            'duration': route_data['duration']
        })


class VehicleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing emergency vehicles.

    Provides CRUD operations and filtering by availability and type.
    """
    queryset = Vehicle.objects.select_related('base_facility', 'current_incident').all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated, IsDispatcherOrReadOnly]
    pagination_class = None  # Disable pagination to preserve GeoJSON FeatureCollection structure
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'vehicle_type']

    @action(detail=False, methods=['get'])
    def available(self, request):
        """
        Get available vehicles, optionally filtered by type.

        GET /api/vehicles/available/?type=ambulance
        """
        vehicle_type = request.query_params.get('type')
        queryset = self.get_queryset().available()

        if vehicle_type:
            queryset = queryset.by_type(vehicle_type)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class DispatchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing dispatch records.

    Read-only access to dispatch history and audit trail.
    """
    queryset = Dispatch.objects.select_related(
        'incident',
        'vehicle',
        'responder',
        'dispatcher'
    ).all()
    serializer_class = DispatchSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['incident', 'vehicle', 'responder']

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """
        Acknowledge dispatch (responder has received notification).

        POST /api/dispatches/{id}/acknowledge/
        """
        dispatch = self.get_object()

        if dispatch.responder != request.user:
            return Response(
                {'error': 'Only assigned responder can acknowledge'},
                status=status.HTTP_403_FORBIDDEN
            )

        if dispatch.acknowledged_at:
            return Response(
                {'error': 'Dispatch already acknowledged'},
                status=status.HTTP_400_BAD_REQUEST
            )

        dispatch.acknowledge()
        serializer = self.get_serializer(dispatch)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def arrive(self, request, pk=None):
        """
        Mark arrival at incident scene.

        POST /api/dispatches/{id}/arrive/
        """
        dispatch = self.get_object()

        if dispatch.responder != request.user:
            return Response(
                {'error': 'Only assigned responder can mark arrival'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not dispatch.acknowledged_at:
            return Response(
                {'error': 'Must acknowledge dispatch first'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if dispatch.arrived_at:
            return Response(
                {'error': 'Already marked as arrived'},
                status=status.HTTP_400_BAD_REQUEST
            )

        dispatch.arrive()
        serializer = self.get_serializer(dispatch)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Mark dispatch as completed.

        POST /api/dispatches/{id}/complete/
        """
        dispatch = self.get_object()

        user = request.user
        profile = getattr(user, 'profile', None)
        is_assigned = dispatch.responder == user
        is_dispatcher = profile and profile.is_dispatcher

        if not (is_assigned or is_dispatcher):
            return Response(
                {'error': 'Only assigned responder or dispatcher can complete'},
                status=status.HTTP_403_FORBIDDEN
            )

        if dispatch.completed_at:
            return Response(
                {'error': 'Dispatch already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        dispatch.complete()
        serializer = self.get_serializer(dispatch)
        return Response(serializer.data)
