"""
API serializers for incident management.

Provides GeoJSON and standard JSON serialization for incidents,
vehicles, and assignments.
"""
from rest_framework import serializers
from rest_framework_gis.fields import GeometryField
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import Incident, Vehicle, VehicleAssignment, DispatcherProfile


class IncidentSerializer(serializers.ModelSerializer):
    """
    Standard serializer for incidents.
    """
    
    location = serializers.SerializerMethodField()
    assigned_vehicles = serializers.SerializerMethodField()
    dispatcher_name = serializers.CharField(source='dispatcher.username', read_only=True)
    
    class Meta:
        model = Incident
        fields = (
            'id',
            'incident_number',
            'incident_type',
            'priority',
            'status',
            'title',
            'description',
            'address',
            'location',
            'reporter_name',
            'reporter_phone',
            'assigned_vehicles',
            'dispatcher',
            'dispatcher_name',
            'reported_at',
            'dispatched_at',
            'arrived_at',
            'resolved_at',
            'notes',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('incident_number', 'created_at', 'updated_at')
    
    def get_location(self, obj):
        if obj.location:
            return {
                'type': 'Point',
                'coordinates': [obj.location.x, obj.location.y]
            }
        return None
    
    def get_assigned_vehicles(self, obj):
        vehicles = obj.assigned_vehicles.all()
        return [{
            'id': v.id,
            'call_sign': v.call_sign,
            'vehicle_type': v.vehicle_type,
            'status': v.status,
        } for v in vehicles]


class IncidentGeoSerializer(GeoFeatureModelSerializer):
    """
    GeoJSON serializer for incidents.
    
    Converts Incident model instances to GeoJSON format for map display.
    """
    
    location = GeometryField()
    
    class Meta:
        model = Incident
        geo_field = 'location'
        fields = (
            'id',
            'incident_number',
            'incident_type',
            'priority',
            'status',
            'title',
            'description',
            'address',
            'reporter_name',
            'reporter_phone',
            'reported_at',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('incident_number', 'created_at', 'updated_at')


class IncidentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new incidents.
    """
    
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)
    
    class Meta:
        model = Incident
        fields = (
            'incident_type',
            'priority',
            'title',
            'description',
            'address',
            'latitude',
            'longitude',
            'reporter_name',
            'reporter_phone',
        )
    
    def create(self, validated_data):
        from django.contrib.gis.geos import Point
        
        lat = validated_data.pop('latitude')
        lon = validated_data.pop('longitude')
        validated_data['location'] = Point(lon, lat, srid=4326)
        
        return super().create(validated_data)


class VehicleSerializer(serializers.ModelSerializer):
    """
    Standard serializer for vehicles.
    """
    
    current_location = serializers.SerializerMethodField()
    home_station_name = serializers.CharField(source='home_station.name', read_only=True)
    current_incident_number = serializers.CharField(
        source='current_incident.incident_number', 
        read_only=True
    )
    
    class Meta:
        model = Vehicle
        fields = (
            'id',
            'call_sign',
            'vehicle_type',
            'registration',
            'make_model',
            'capacity',
            'status',
            'current_location',
            'home_station',
            'home_station_name',
            'current_incident',
            'current_incident_number',
            'location_updated_at',
            'equipment',
            'capabilities',
            'notes',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')
    
    def get_current_location(self, obj):
        if obj.current_location:
            return {
                'type': 'Point',
                'coordinates': [obj.current_location.x, obj.current_location.y]
            }
        return None


class VehicleGeoSerializer(GeoFeatureModelSerializer):
    """
    GeoJSON serializer for vehicles.
    
    Converts Vehicle model instances to GeoJSON format for map display.
    """
    
    current_location = GeometryField()
    home_station_name = serializers.CharField(source='home_station.name', read_only=True)
    
    class Meta:
        model = Vehicle
        geo_field = 'current_location'
        fields = (
            'id',
            'call_sign',
            'vehicle_type',
            'status',
            'registration',
            'home_station_name',
            'location_updated_at',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')


class VehicleLocationUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating vehicle location.
    """
    
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)


class VehicleAssignmentSerializer(serializers.ModelSerializer):
    """
    Serializer for vehicle assignments.
    """
    
    vehicle_call_sign = serializers.CharField(source='vehicle.call_sign', read_only=True)
    vehicle_type = serializers.CharField(source='vehicle.vehicle_type', read_only=True)
    incident_number = serializers.CharField(source='incident.incident_number', read_only=True)
    assigned_by_username = serializers.CharField(source='assigned_by.username', read_only=True)
    response_time_seconds = serializers.SerializerMethodField()
    
    class Meta:
        model = VehicleAssignment
        fields = (
            'id',
            'incident',
            'incident_number',
            'vehicle',
            'vehicle_call_sign',
            'vehicle_type',
            'assigned_at',
            'dispatched_at',
            'en_route_at',
            'arrived_at',
            'completed_at',
            'assigned_by',
            'assigned_by_username',
            'route_distance_m',
            'route_duration_s',
            'response_time_seconds',
            'notes',
        )
        read_only_fields = ('assigned_at', 'assigned_by')
    
    def get_response_time_seconds(self, obj):
        rt = obj.response_time
        return rt.total_seconds() if rt else None


class DispatcherProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for dispatcher profiles.
    """
    
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    active_incidents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DispatcherProfile
        fields = (
            'id',
            'username',
            'email',
            'badge_number',
            'is_on_duty',
            'shift_start',
            'shift_end',
            'incidents_handled',
            'active_incidents_count',
        )
    
    def get_active_incidents_count(self, obj):
        return obj.user.dispatched_incidents.filter(
            status__in=['pending', 'dispatched', 'en_route', 'on_scene']
        ).count()
