"""
Base test case for spatial API tests.

Provides common setup and helper methods for testing GeoJSON endpoints.
"""
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.test import TestCase
from rest_framework.test import APIClient

from boundaries.models import County

User = get_user_model()


class SpatialAPITestCase(TestCase):
    """
    Base test case for spatial API endpoints.
    
    Provides:
    - Test client (self.client)
    - Test county (self.county) - Dublin county for testing
    - Staff user (self.staff_user) - For authenticated tests
    - Helper method unwrap_features() - Extract features from GeoJSON responses
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        
        # Create a test county (Dublin) for spatial queries
        # Using a simple bounding box polygon for Dublin area
        dublin_bbox = Polygon(
            (
                (-6.4, 53.2),  # Southwest
                (-6.4, 53.5),  # Northwest
                (-6.1, 53.5),  # Northeast
                (-6.1, 53.2),  # Southeast
                (-6.4, 53.2),  # Close polygon
            ),
            srid=4326,
        )
        self.county = County.objects.create(
            name_en='Dublin',
            name_local='Baile Átha Cliath',
            iso_code='IE-D',
            geom=MultiPolygon(dublin_bbox, srid=4326),
        )
        
        # Create a staff user for authenticated tests
        self.staff_user = User.objects.create_user(
            username='teststaff',
            email='staff@test.com',
            password='testpass123',
            is_staff=True,
        )
    
    def unwrap_features(self, geojson_data):
        """
        Extract features from GeoJSON response.
        
        Handles both FeatureCollection and direct Feature/array responses.
        
        Args:
            geojson_data: GeoJSON response data (dict or list)
            
        Returns:
            List of feature dictionaries
        """
        if isinstance(geojson_data, list):
            # Direct array of features
            return geojson_data
        elif isinstance(geojson_data, dict):
            if geojson_data.get('type') == 'FeatureCollection':
                return geojson_data.get('features', [])
            elif geojson_data.get('type') == 'Feature':
                return [geojson_data]
            elif 'results' in geojson_data:
                # Paginated response with results array
                return geojson_data.get('results', [])
        return []
