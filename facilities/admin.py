"""
Django admin configuration for emergency facilities.

Provides geographic admin interface for County and EmergencyFacility models
with search, filtering, and map visualization capabilities.
"""
from django.contrib.gis import admin

from .models import County, EmergencyFacility


@admin.register(County)
class CountyAdmin(admin.GISModelAdmin):
    """Admin interface for county boundaries with map display."""
    list_display = ('id', 'name_en', 'iso_code')
    search_fields = ('name_en', 'iso_code')
    list_filter = ('iso_code',)


@admin.register(EmergencyFacility)
class EmergencyFacilityAdmin(admin.GISModelAdmin):
    """Admin interface for emergency facilities with map display."""
    list_display = ('id', 'name', 'type', 'updated_at')
    list_filter = ('type',)
    search_fields = ('name', 'address',)
