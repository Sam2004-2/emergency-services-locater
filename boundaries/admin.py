from django.contrib.gis import admin

from .models import County


@admin.register(County)
class CountyAdmin(admin.GISModelAdmin):
    list_display = ('id', 'name_en', 'iso_code')
    search_fields = ('name_en', 'iso_code')
    list_filter = ('iso_code',)
