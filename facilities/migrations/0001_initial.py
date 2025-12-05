"""
Initial migration for facilities app.

This migration uses db_table settings to point to existing tables
from the boundaries and services apps, avoiding data migration.
"""
import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='County',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_id', models.CharField(blank=True, help_text='Original source identifier', max_length=100, null=True)),
                ('name_en', models.CharField(db_index=True, help_text='County name in English', max_length=100)),
                ('name_local', models.CharField(blank=True, help_text='County name in local language', max_length=100, null=True)),
                ('iso_code', models.CharField(blank=True, help_text='ISO 3166-2 code', max_length=10, null=True, unique=True)),
                ('geom', django.contrib.gis.db.models.fields.MultiPolygonField(help_text='County boundary (WGS84)', srid=4326, spatial_index=True)),
            ],
            options={
                'verbose_name': 'County',
                'verbose_name_plural': 'Counties',
                'db_table': 'boundaries_county',
                'ordering': ['name_en'],
            },
        ),
        migrations.CreateModel(
            name='EmergencyFacility',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Facility name', max_length=200)),
                ('type', models.CharField(choices=[('hospital', 'Hospital'), ('fire_station', 'Fire Station'), ('police_station', 'Police Station'), ('ambulance_base', 'Ambulance Base')], db_index=True, max_length=32)),
                ('address', models.CharField(blank=True, max_length=500, null=True)),
                ('phone', models.CharField(blank=True, max_length=50, null=True)),
                ('website', models.URLField(blank=True, max_length=500, null=True)),
                ('properties', models.JSONField(blank=True, default=dict, help_text='Additional metadata')),
                ('geom', django.contrib.gis.db.models.fields.PointField(help_text='Facility location (WGS84)', srid=4326, spatial_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Emergency Facility',
                'verbose_name_plural': 'Emergency Facilities',
                'db_table': 'services_emergencyfacility',
                'ordering': ['name'],
            },
        ),
        migrations.AddIndex(
            model_name='emergencyfacility',
            index=models.Index(fields=['type', 'created_at'], name='services_em_type_0e6d2b_idx'),
        ),
    ]
