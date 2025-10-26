from django.contrib.gis import admin

from .models import EmergencyFacility


@admin.register(EmergencyFacility)
class EmergencyFacilityAdmin(admin.GISModelAdmin):
    list_display = ('id', 'name', 'type', 'updated_at')
    list_filter = ('type',)
    search_fields = ('name', 'address',)
