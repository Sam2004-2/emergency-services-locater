"""
Shared test utilities for facilities app.

Provides base test classes with spatial data fixtures for testing
API endpoints and model behavior.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.db import connection
from django.test import TestCase

from facilities.models import County, EmergencyFacility


class SpatialAPITestCase(TestCase):
    """Shared setup for API tests requiring spatial schema and seed data."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls._ensure_extensions()
        cls._ensure_groups()
        # Schema is created by Django migrations, no SQL files needed
        cls.county = cls._ensure_demo_county()
        cls.staff_user = cls._create_staff_user()
        cls._ensure_demo_facilities()

    @classmethod
    def _ensure_extensions(cls):
        """Ensure required PostGIS extensions are enabled."""
        extensions = ['postgis', 'pg_trgm']
        with connection.cursor() as cursor:
            for ext in extensions:
                cursor.execute(f"CREATE EXTENSION IF NOT EXISTS {ext};")

    @classmethod
    def _ensure_groups(cls):
        """Ensure required groups exist."""
        Group.objects.get_or_create(name='Editors')
        Group.objects.get_or_create(name='Viewers')

    @classmethod
    def _ensure_demo_county(cls):
        County.objects.all().delete()
        polygon = Polygon(
            (
                (-6.55, 53.15),
                (-6.55, 53.55),
                (-5.95, 53.55),
                (-5.95, 53.15),
                (-6.55, 53.15),
            ),
            srid=4326,
        )
        county = County.objects.create(
            source_id='demo',
            name_en='Dublin',
            name_local='Baile Átha Cliath',
            iso_code='IE-D',
            geom=MultiPolygon(polygon, srid=4326),
        )
        return county

    @classmethod
    def _ensure_demo_facilities(cls):
        """Create demo facilities for testing."""
        EmergencyFacility.objects.all().delete()
        facilities = [
            EmergencyFacility(
                name='Dublin Hospital',
                type='hospital',
                address='123 Main St, Dublin',
                geom=Point(-6.26, 53.35, srid=4326),
            ),
            EmergencyFacility(
                name='Dublin Fire Station',
                type='fire_station',
                address='456 Fire Lane, Dublin',
                geom=Point(-6.28, 53.36, srid=4326),
            ),
            EmergencyFacility(
                name='Dublin Police Station',
                type='police_station',
                address='789 Police Ave, Dublin',
                geom=Point(-6.25, 53.34, srid=4326),
            ),
            EmergencyFacility(
                name='Dublin Ambulance Base',
                type='ambulance_base',
                address='101 Emergency Rd, Dublin',
                geom=Point(-6.27, 53.33, srid=4326),
            ),
        ]
        EmergencyFacility.objects.bulk_create(facilities)

    @classmethod
    def _create_staff_user(cls):
        User = get_user_model()
        user = User.objects.create_user(
            username='testrunner',
            password='Pass1234!',
            is_staff=True,
        )
        # Add to Editors group for role-based permissions
        editors_group = Group.objects.get(name='Editors')
        user.groups.add(editors_group)
        # Also add model-level permissions for backwards compatibility
        perms = Permission.objects.filter(
            codename__in=[
                'add_emergencyfacility',
                'change_emergencyfacility',
                'delete_emergencyfacility',
            ]
        )
        user.user_permissions.add(*perms)
        return user

    def unwrap_features(self, payload):
        if isinstance(payload, dict):
            if payload.get('type') == 'FeatureCollection':
                return payload.get('features', [])
            results = payload.get('results')
            if isinstance(results, dict) and results.get('type') == 'FeatureCollection':
                return results.get('features', [])
        return []
