"""
Serializers for incident management API.

Provides DRF serializers for incidents, vehicles, and dispatch records
with nested relationships and spatial field support.
"""
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import Dispatch, Incident, Vehicle


class IncidentSerializer(GeoFeatureModelSerializer):
    """Serializer for Incident model with GeoJSON support."""

    # Explicitly declare GeometryField for proper GeoJSON serialization
    location = GeometryField(read_only=True)
    
    incident_type_display = serializers.CharField(
        source='get_incident_type_display',
        read_only=True
    )
    severity_display = serializers.CharField(
        source='get_severity_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    reported_by_name = serializers.SerializerMethodField()
    assigned_responder_name = serializers.SerializerMethodField()
    nearest_facility_name = serializers.SerializerMethodField()
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Incident
        geo_field = 'location'
        fields = [
            'id', 'title', 'description', 'incident_type', 'incident_type_display',
            'severity', 'severity_display', 'status', 'status_display',
            'address', 'reported_by', 'reported_by_name',
            'assigned_responder', 'assigned_responder_name',
            'nearest_facility', 'nearest_facility_name',
            'route_geometry', 'route_distance_m', 'route_duration_s',
            'created_at', 'updated_at', 'dispatched_at', 'resolved_at',
            'is_active'
        ]
        read_only_fields = ['created_at', 'updated_at', 'is_active']

    def get_reported_by_name(self, obj):
        """Get reporter's full name or username."""
        if obj.reported_by:
            return obj.reported_by.get_full_name() or obj.reported_by.username
        return None

    def get_assigned_responder_name(self, obj):
        """Get assigned responder's full name or username."""
        if obj.assigned_responder:
            return obj.assigned_responder.get_full_name() or obj.assigned_responder.username
        return None

    def get_nearest_facility_name(self, obj):
        """Get nearest facility name."""
        if obj.nearest_facility:
            return obj.nearest_facility.name
        return None


class IncidentListSerializer(GeoFeatureModelSerializer):
    """Lightweight serializer for incident lists."""

    # Explicitly declare GeometryField for proper GeoJSON serialization
    location = GeometryField(read_only=True)

    incident_type_display = serializers.CharField(
        source='get_incident_type_display',
        read_only=True
    )
    severity_display = serializers.CharField(
        source='get_severity_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta:
        model = Incident
        geo_field = 'location'
        fields = [
            'id', 'title', 'incident_type', 'incident_type_display',
            'severity', 'severity_display', 'status', 'status_display',
            'address', 'created_at', 'dispatched_at'
        ]


class VehicleSerializer(GeoFeatureModelSerializer):
    """Serializer for Vehicle model with GeoJSON support."""

    # Explicitly declare GeometryField for proper GeoJSON serialization
    current_position = GeometryField(read_only=True)

    vehicle_type_display = serializers.CharField(
        source='get_vehicle_type_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    base_facility_name = serializers.SerializerMethodField()
    current_incident_id = serializers.PrimaryKeyRelatedField(
        source='current_incident',
        read_only=True
    )
    is_available = serializers.ReadOnlyField()

    class Meta:
        model = Vehicle
        geo_field = 'current_position'
        fields = [
            'id', 'callsign', 'vehicle_type', 'vehicle_type_display',
            'status', 'status_display', 'heading', 'speed_kmh',
            'base_facility', 'base_facility_name',
            'current_incident_id', 'is_available',
            'created_at', 'updated_at', 'last_position_update'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_position_update', 'is_available']

    def get_base_facility_name(self, obj):
        """Get base facility name."""
        if obj.base_facility:
            return obj.base_facility.name
        return None


class DispatchSerializer(serializers.ModelSerializer):
    """Serializer for Dispatch records."""

    incident_title = serializers.CharField(source='incident.title', read_only=True)
    vehicle_callsign = serializers.CharField(source='vehicle.callsign', read_only=True)
    responder_name = serializers.SerializerMethodField()
    dispatcher_name = serializers.SerializerMethodField()
    route_geometry_geojson = serializers.SerializerMethodField()

    class Meta:
        model = Dispatch
        fields = [
            'id', 'incident', 'incident_title', 'vehicle', 'vehicle_callsign',
            'responder', 'responder_name', 'dispatcher', 'dispatcher_name',
            'origin', 'destination', 'route_geometry', 'route_geometry_geojson',
            'route_distance_m', 'route_duration_s',
            'created_at', 'acknowledged_at', 'arrived_at', 'completed_at',
            'notes'
        ]
        read_only_fields = ['created_at']

    def get_responder_name(self, obj):
        """Get responder's full name or username."""
        if obj.responder:
            return obj.responder.get_full_name() or obj.responder.username
        return None

    def get_dispatcher_name(self, obj):
        """Get dispatcher's full name or username."""
        if obj.dispatcher:
            return obj.dispatcher.get_full_name() or obj.dispatcher.username
        return None

    def get_route_geometry_geojson(self, obj):
        """Convert route geometry to GeoJSON."""
        if obj.route_geometry:
            return {
                'type': 'LineString',
                'coordinates': list(obj.route_geometry.coords)
            }
        return None
