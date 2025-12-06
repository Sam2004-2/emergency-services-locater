"""Admin configuration for incident management."""
from django.contrib.gis import admin

from .models import Dispatch, Incident, Vehicle


@admin.register(Incident)
class IncidentAdmin(admin.GISModelAdmin):
    """Admin interface for incidents with map widget."""
    list_display = (
        'id', 'title', 'incident_type', 'severity',
        'status', 'created_at', 'assigned_responder'
    )
    list_filter = ('incident_type', 'severity', 'status')
    search_fields = ('title', 'description', 'address')
    readonly_fields = ('created_at', 'updated_at', 'dispatched_at', 'resolved_at')
    raw_id_fields = ('reported_by', 'assigned_responder', 'nearest_facility')
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'incident_type', 'severity', 'status')
        }),
        ('Location', {
            'fields': ('location', 'address', 'nearest_facility')
        }),
        ('Assignment', {
            'fields': ('reported_by', 'assigned_responder')
        }),
        ('Route Data', {
            'fields': ('route_geometry', 'route_distance_m', 'route_duration_s'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'dispatched_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Vehicle)
class VehicleAdmin(admin.GISModelAdmin):
    """Admin interface for vehicles with map widget."""
    list_display = (
        'callsign', 'vehicle_type', 'status',
        'base_facility', 'current_incident', 'last_position_update'
    )
    list_filter = ('vehicle_type', 'status')
    search_fields = ('callsign',)
    readonly_fields = ('created_at', 'updated_at', 'last_position_update')
    raw_id_fields = ('base_facility', 'current_incident')

    fieldsets = (
        (None, {
            'fields': ('callsign', 'vehicle_type', 'status')
        }),
        ('Position', {
            'fields': ('current_position', 'heading', 'speed_kmh')
        }),
        ('Assignment', {
            'fields': ('base_facility', 'current_incident')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_position_update'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Dispatch)
class DispatchAdmin(admin.GISModelAdmin):
    """Admin interface for dispatch records."""
    list_display = (
        'id', 'incident', 'vehicle', 'responder',
        'dispatcher', 'created_at', 'acknowledged_at', 'completed_at'
    )
    list_filter = ('created_at',)
    search_fields = ('incident__title', 'vehicle__callsign', 'notes')
    readonly_fields = (
        'created_at', 'acknowledged_at', 'arrived_at', 'completed_at'
    )
    raw_id_fields = ('incident', 'vehicle', 'responder', 'dispatcher')

    fieldsets = (
        (None, {
            'fields': ('incident', 'vehicle', 'responder', 'dispatcher')
        }),
        ('Route', {
            'fields': ('origin', 'destination', 'route_geometry',
                      'route_distance_m', 'route_duration_s')
        }),
        ('Status', {
            'fields': ('created_at', 'acknowledged_at', 'arrived_at', 'completed_at')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )
