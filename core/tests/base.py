from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.db import connection
from django.test import TestCase

from boundaries.models import County


class SpatialAPITestCase(TestCase):
    """Shared setup for API tests requiring spatial schema and seed data."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls._ensure_extensions()
        cls._load_sql('db/schema/010_bounds_counties.sql')
        cls._load_sql('db/schema/020_services_facilities.sql')
        cls._load_sql('db/schema/040_constraints_indexes.sql')
        cls._load_sql('db/import/seed_facilities.sql')
        cls.county = cls._ensure_demo_county()
        cls.staff_user = cls._create_staff_user()

    @classmethod
    def _run_sql(cls, sql_text: str):
        if not sql_text.strip():
            return
        with connection.cursor() as cursor:
            cursor.execute(sql_text)

    @classmethod
    def _load_sql(cls, relative_path: str):
        sql_path = Path(settings.BASE_DIR) / relative_path
        if not sql_path.exists():
            return
        cls._run_sql(sql_path.read_text())

    @classmethod
    def _ensure_extensions(cls):
        extensions = [
            'postgis',
            'postgis_topology',
            'fuzzystrmatch',
            'postgis_tiger_geocoder',
            'pg_trgm',
        ]
        with connection.cursor() as cursor:
            for ext in extensions:
                try:
                    cursor.execute(f"CREATE EXTENSION IF NOT EXISTS {ext};")
                except Exception:
                    if ext in {'postgis', 'pg_trgm'}:
                        raise
                    continue

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
            id=1,
            source_id='demo',
            name_en='Dublin',
            name_local='Baile Átha Cliath',
            iso_code='IE-D',
            geom=MultiPolygon(polygon, srid=4326),
        )
        return county

    @classmethod
    def _create_staff_user(cls):
        User = get_user_model()
        user = User.objects.create_user(
            username='testrunner',
            password='Pass1234!',
            is_staff=True,
        )
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
