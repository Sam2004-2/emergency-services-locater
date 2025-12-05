"""
REST API endpoints for incident management system.

Provides endpoints for:
- Incident CRUD and lifecycle management
- Vehicle management and location updates
- Routing calculations
- Coverage analysis
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db.models import Q
from django.utils import timezone

from .models import Incident, Vehicle, VehicleAssignment, DispatcherProfile
from .serializers import (
    IncidentSerializer, IncidentCreateSerializer, IncidentGeoSerializer,
    VehicleSerializer, VehicleGeoSerializer, VehicleLocationUpdateSerializer,
    VehicleAssignmentSerializer, DispatcherProfileSerializer
)
from .routing import routing_service
from .coverage import coverage_analyzer


class IncidentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing incidents.
    
    Endpoints:
        GET /api/incidents/ - List all incidents
        POST /api/incidents/ - Create new incident
        GET /api/incidents/{id}/ - Retrieve incident
        PATCH /api/incidents/{id}/ - Update incident
        DELETE /api/incidents/{id}/ - Delete incident (soft delete)
        
    Actions:
        POST /api/incidents/{id}/assign-vehicle/ - Assign vehicle to incident
        POST /api/incidents/{id}/resolve/ - Mark incident as resolved
        GET /api/incidents/active/ - List active incidents
        GET /api/incidents/geojson/ - Get incidents as GeoJSON
    """
    queryset = Incident.objects.select_related('dispatcher').prefetch_related('assigned_vehicles').all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return IncidentCreateSerializer
        if self.action in ['geojson', 'list_geojson']:
            return IncidentGeoSerializer
        return IncidentSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by incident type
        incident_type = self.request.query_params.get('type')
        if incident_type:
            queryset = queryset.filter(incident_type=incident_type)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(reported_at__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(reported_at__lte=date_to)
        
        return queryset.order_by('-reported_at')
    
    def perform_create(self, serializer):
        """Set the dispatcher on creation if user is authenticated."""
        serializer.save(dispatcher=self.request.user)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active incidents (pending, dispatched, en_route, on_scene)."""
        active_statuses = ['pending', 'dispatched', 'en_route', 'on_scene']
        queryset = self.get_queryset().filter(status__in=active_statuses)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def geojson(self, request):
        """Get incidents as GeoJSON FeatureCollection."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = IncidentGeoSerializer(queryset, many=True)
        
        return Response({
            'type': 'FeatureCollection',
            'features': serializer.data,
        })
    
    @action(detail=True, methods=['post'], url_path='assign-vehicle')
    def assign_vehicle(self, request, pk=None):
        """
        Assign a vehicle to this incident.
        
        Request body:
            vehicle_id: ID of vehicle to assign
            notes: Optional dispatch notes
        """
        incident = self.get_object()
        vehicle_id = request.data.get('vehicle_id')
        notes = request.data.get('notes', '')
        
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
        
        if vehicle.status != 'available':
            return Response(
                {'error': f'Vehicle is not available (status: {vehicle.status})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate route
        route_info = None
        if vehicle.current_location and incident.location:
            vehicle_loc = (vehicle.current_location.y, vehicle.current_location.x)
            incident_loc = (incident.location.y, incident.location.x)
            route = routing_service.calculate_route(vehicle_loc, incident_loc)
            if route:
                route_info = route.to_dict()
        
        # Create assignment
        assignment = VehicleAssignment.objects.create(
            incident=incident,
            vehicle=vehicle,
            assigned_by=request.user,
            notes=notes,
            route_geometry=route_info.get('geometry') if route_info else None,
            route_distance_m=route_info.get('distance_m') if route_info else None,
            route_duration_s=route_info.get('duration_s') if route_info else None,
        )
        
        # Update incident and vehicle status
        incident.status = 'dispatched'
        incident.dispatcher = request.user
        incident.dispatched_at = timezone.now()
        incident.save()
        
        vehicle.status = 'dispatched'
        vehicle.current_incident = incident
        vehicle.save()
        
        return Response({
            'message': 'Vehicle assigned successfully',
            'assignment': VehicleAssignmentSerializer(assignment).data,
            'route': route_info,
        })
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark incident as resolved."""
        incident = self.get_object()
        
        if incident.status == 'resolved':
            return Response(
                {'error': 'Incident is already resolved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        incident.status = 'resolved'
        incident.resolved_at = timezone.now()
        incident.save()
        
        # Release assigned vehicles
        for vehicle in incident.assigned_vehicles.all():
            vehicle.status = 'available'
            vehicle.current_incident = None
            vehicle.save()
            
            # Complete the assignment
            assignment = VehicleAssignment.objects.filter(
                incident=incident,
                vehicle=vehicle,
                completed_at__isnull=True
            ).first()
            if assignment:
                assignment.completed_at = timezone.now()
                assignment.save()
        
        return Response({
            'message': 'Incident resolved',
            'incident': IncidentSerializer(incident).data,
        })
    
    @action(detail=True, methods=['get'], url_path='nearby-vehicles')
    def nearby_vehicles(self, request, pk=None):
        """Find nearby available vehicles for this incident."""
        incident = self.get_object()
        max_results = int(request.query_params.get('limit', 5))
        
        available_vehicles = Vehicle.objects.filter(
            status='available',
            current_location__isnull=False
        )
        
        incident_location = (incident.location.y, incident.location.x)
        results = routing_service.find_nearest_vehicles(
            incident_location,
            list(available_vehicles),
            max_results
        )
        
        return Response({
            'incident_id': incident.id,
            'incident_number': incident.incident_number,
            'available_vehicles': results,
        })


class VehicleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing vehicles.
    
    Endpoints:
        GET /api/vehicles/ - List all vehicles
        POST /api/vehicles/ - Create new vehicle
        GET /api/vehicles/{id}/ - Retrieve vehicle
        PATCH /api/vehicles/{id}/ - Update vehicle
        PATCH /api/vehicles/{id}/location/ - Update vehicle location
        
    Actions:
        GET /api/vehicles/available/ - List available vehicles
        GET /api/vehicles/geojson/ - Get vehicles as GeoJSON
    """
    queryset = Vehicle.objects.select_related('home_station', 'current_incident').all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'update_location':
            return VehicleLocationUpdateSerializer
        if self.action in ['geojson']:
            return VehicleGeoSerializer
        return VehicleSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by type
        vehicle_type = self.request.query_params.get('type')
        if vehicle_type:
            queryset = queryset.filter(vehicle_type=vehicle_type)
        
        # Filter by home station
        station_id = self.request.query_params.get('station')
        if station_id:
            queryset = queryset.filter(home_station_id=station_id)
        
        return queryset.order_by('call_sign')
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get all available vehicles."""
        queryset = self.get_queryset().filter(status='available')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def geojson(self, request):
        """Get vehicles as GeoJSON FeatureCollection."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = VehicleGeoSerializer(queryset, many=True)
        
        return Response({
            'type': 'FeatureCollection',
            'features': serializer.data,
        })
    
    @action(detail=True, methods=['patch'], url_path='location')
    def update_location(self, request, pk=None):
        """
        Update vehicle location.
        
        Request body:
            latitude: float
            longitude: float
        """
        vehicle = self.get_object()
        serializer = VehicleLocationUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        vehicle.current_location = Point(
            serializer.validated_data['longitude'],
            serializer.validated_data['latitude'],
            srid=4326
        )
        vehicle.location_updated_at = timezone.now()
        vehicle.save()
        
        return Response({
            'message': 'Location updated',
            'vehicle': VehicleSerializer(vehicle).data,
        })


class RoutingViewSet(viewsets.ViewSet):
    """
    ViewSet for routing operations.
    
    Endpoints:
        POST /api/routing/calculate/ - Calculate route between two points
        POST /api/routing/optimize-assignment/ - Find optimal vehicle assignment
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """
        Calculate route between two points.
        
        Request body:
            origin: {latitude: float, longitude: float}
            destination: {latitude: float, longitude: float}
        """
        origin = request.data.get('origin')
        destination = request.data.get('destination')
        
        if not origin or not destination:
            return Response(
                {'error': 'Both origin and destination are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            origin_coords = (origin['latitude'], origin['longitude'])
            dest_coords = (destination['latitude'], destination['longitude'])
        except (KeyError, TypeError):
            return Response(
                {'error': 'Invalid coordinate format. Expected {latitude, longitude}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        route = routing_service.calculate_route(origin_coords, dest_coords)
        
        if route:
            return Response(route.to_dict())
        else:
            return Response(
                {'error': 'Could not calculate route'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='optimize-assignment')
    def optimize_assignment(self, request):
        """
        Find optimal vehicle assignment for an incident.
        
        Request body:
            incident_id: int (optional, provide location if not using incident)
            location: {latitude: float, longitude: float} (optional)
            vehicle_types: [str] (optional, list of required vehicle types)
        """
        incident_id = request.data.get('incident_id')
        location = request.data.get('location')
        vehicle_types = request.data.get('vehicle_types', [])
        
        if incident_id:
            try:
                incident = Incident.objects.get(id=incident_id)
                location_coords = (incident.location.y, incident.location.x)
            except Incident.DoesNotExist:
                return Response(
                    {'error': 'Incident not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        elif location:
            try:
                location_coords = (location['latitude'], location['longitude'])
            except (KeyError, TypeError):
                return Response(
                    {'error': 'Invalid location format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {'error': 'Either incident_id or location is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        available_vehicles = Vehicle.objects.filter(
            status='available',
            current_location__isnull=False
        )
        
        assignments = routing_service.optimize_assignment(
            location_coords,
            list(available_vehicles),
            vehicle_types if vehicle_types else None
        )
        
        return Response({
            'location': {
                'latitude': location_coords[0],
                'longitude': location_coords[1],
            },
            'recommended_assignments': assignments,
        })


class CoverageViewSet(viewsets.ViewSet):
    """
    ViewSet for coverage analysis.
    
    Endpoints:
        GET /api/coverage/analyze/ - Analyze coverage for area
        GET /api/coverage/vehicles/ - Real-time vehicle coverage
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def analyze(self, request):
        """
        Analyze emergency service coverage.
        
        Query parameters:
            county_id: int (optional)
            facility_types: comma-separated list (optional)
            response_times: comma-separated list of minutes (optional)
        """
        county_id = request.query_params.get('county_id')
        facility_types = request.query_params.get('facility_types')
        response_times = request.query_params.get('response_times')
        
        # Parse parameters
        if county_id:
            county_id = int(county_id)
        
        if facility_types:
            facility_types = [ft.strip() for ft in facility_types.split(',')]
        
        if response_times:
            response_times = [int(rt.strip()) for rt in response_times.split(',')]
        
        results = coverage_analyzer.analyze_coverage(
            county_id=county_id,
            facility_types=facility_types,
            response_times=response_times
        )
        
        return Response(results)
    
    @action(detail=False, methods=['get'])
    def vehicles(self, request):
        """
        Get real-time vehicle coverage.
        
        Query parameters:
            vehicle_type: str (optional)
            response_time: int (optional, minutes, default 10)
        """
        vehicle_type = request.query_params.get('vehicle_type')
        response_time = int(request.query_params.get('response_time', 10))
        
        results = coverage_analyzer.get_vehicle_coverage(
            vehicle_type=vehicle_type,
            response_time=response_time
        )
        
        return Response(results)
