"""
Django admin interface for incident management.
"""
from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django.utils.html import format_html

from .models import Incident, Vehicle, VehicleAssignment, DispatcherProfile


@admin.register(Incident)
class IncidentAdmin(GISModelAdmin):
    """Admin interface for incidents."""
    
    list_display = [
        'incident_number', 'incident_type', 'priority_badge', 'status_badge',
        'title', 'address', 'reported_at'
    ]
    list_filter = ['status', 'priority', 'incident_type', 'reported_at']
    search_fields = ['incident_number', 'title', 'address', 'description', 'reporter_phone']
    readonly_fields = ['incident_number', 'created_at', 'updated_at']
    date_hierarchy = 'reported_at'
    
    fieldsets = (
        ('Incident Details', {
            'fields': ('incident_number', 'incident_type', 'priority', 'status', 'title', 'description')
        }),
        ('Location', {
            'fields': ('location', 'address')
        }),
        ('Reporter Information', {
            'fields': ('reporter_name', 'reporter_phone')
        }),
        ('Dispatch', {
            'fields': ('dispatcher',)
        }),
        ('Timestamps', {
            'fields': ('reported_at', 'dispatched_at', 'arrived_at', 'resolved_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes', 'properties'),
            'classes': ('collapse',)
        }),
    )
    
    def priority_badge(self, obj):
        colors = {
            'critical': '#dc3545',
            'high': '#fd7e14',
            'medium': '#ffc107',
            'low': '#28a745',
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            color, obj.priority.upper()
        )
    priority_badge.short_description = 'Priority'
    priority_badge.admin_order_field = 'priority'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'dispatched': '#17a2b8',
            'en_route': '#6f42c1',
            'on_scene': '#007bff',
            'resolved': '#28a745',
            'cancelled': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'


@admin.register(Vehicle)
class VehicleAdmin(GISModelAdmin):
    """Admin interface for vehicles."""
    
    list_display = [
        'call_sign', 'vehicle_type', 'status_badge', 'home_station',
        'location_updated_at'
    ]
    list_filter = ['status', 'vehicle_type']
    search_fields = ['call_sign', 'registration']
    
    fieldsets = (
        ('Vehicle Details', {
            'fields': ('call_sign', 'vehicle_type', 'registration', 'make_model', 'capacity')
        }),
        ('Status', {
            'fields': ('status', 'home_station', 'current_incident')
        }),
        ('Location', {
            'fields': ('current_location', 'location_updated_at')
        }),
        ('Equipment', {
            'fields': ('equipment', 'capabilities'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes', 'properties'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'available': '#28a745',
            'dispatched': '#17a2b8',
            'en_route': '#6f42c1',
            'on_scene': '#007bff',
            'returning': '#fd7e14',
            'out_of_service': '#dc3545',
            'maintenance': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'


@admin.register(VehicleAssignment)
class VehicleAssignmentAdmin(admin.ModelAdmin):
    """Admin interface for vehicle assignments."""
    
    list_display = [
        'id', 'incident', 'vehicle', 'assigned_by',
        'assigned_at', 'completed_at', 'is_active'
    ]
    list_filter = ['assigned_at', 'completed_at']
    search_fields = ['incident__incident_number', 'vehicle__call_sign']
    readonly_fields = ['assigned_at']
    
    def is_active(self, obj):
        return obj.completed_at is None
    is_active.boolean = True
    is_active.short_description = 'Active'


@admin.register(DispatcherProfile)
class DispatcherProfileAdmin(admin.ModelAdmin):
    """Admin interface for dispatcher profiles."""
    
    list_display = ['user', 'badge_number', 'is_on_duty', 'incidents_handled']
    list_filter = ['is_on_duty']
    search_fields = ['user__username', 'user__email', 'badge_number']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Dispatcher Details', {
            'fields': ('badge_number', 'is_on_duty')
        }),
        ('Shift', {
            'fields': ('shift_start', 'shift_end')
        }),
        ('Stats', {
            'fields': ('incidents_handled',)
        }),
    )
