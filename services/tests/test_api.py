import json

from django.contrib.gis.geos import Polygon
from django.urls import reverse
from rest_framework import status

from core.tests.base import SpatialAPITestCase
from services.models import EmergencyFacility


class FacilityAPITests(SpatialAPITestCase):
    """API regression tests for emergency facilities."""

    def test_list_facilities_geojson(self):
        resp = self.client.get(reverse('facility-list'), {'type': 'hospital'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        features = self.unwrap_features(resp.json())
        self.assertGreaterEqual(len(features), 1)
        self.assertEqual(features[0]['type'], 'Feature')

    def test_nearest_facilities(self):
        resp = self.client.get(
            reverse('facility-nearest'),
            {'lat': 53.3498, 'lon': -6.2603, 'limit': 3},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        features = self.unwrap_features(resp.json())
        self.assertEqual(len(features), 3)

    def test_within_radius_limits(self):
        resp = self.client.get(
            reverse('facility-within-radius'),
            {'lat': 53.3498, 'lon': -6.2603, 'radius_m': 10000},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        features = self.unwrap_features(resp.json())
        self.assertGreaterEqual(len(features), 1)

    def test_within_county_filters_by_id(self):
        resp = self.client.get(
            reverse('facility-within-county'),
            {'id': self.county.id},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        features = self.unwrap_features(resp.json())
        self.assertGreaterEqual(len(features), 1)

    def test_within_county_missing_param(self):
        resp = self.client.get(reverse('facility-within-county'))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_polygon_query(self):
        poly = Polygon(
            (
                (-6.4, 53.2),
                (-6.4, 53.4),
                (-6.1, 53.4),
                (-6.1, 53.2),
                (-6.4, 53.2),
            ),
            srid=4326,
        )
        geometry = json.loads(poly.geojson)
        resp = self.client.post(
            reverse('facility-within-polygon'),
            data={'geometry': geometry},
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        features = self.unwrap_features(resp.json())
        self.assertGreaterEqual(len(features), 1)

    def test_coverage_buffers_response(self):
        resp = self.client.get(
            reverse('facility-coverage-buffers'),
            {'lat': 53.3498, 'lon': -6.2603, 'radius_m': 10000},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn('radius_m', data)
        self.assertIn('results', data)

    def test_create_requires_authentication(self):
        feature = {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [-6.2, 53.34]},
            'properties': {
                'name': 'Unauthorized Facility',
                'type': 'hospital',
            },
        }
        resp = self.client.post(
            reverse('facility-list'),
            data=feature,
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_crud_flow(self):
        self.client.force_login(self.staff_user)
        feature = {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [-6.21, 53.33]},
            'properties': {
                'name': 'Test Facility',
                'type': 'hospital',
                'address': 'Test Address',
            },
        }
        create_resp = self.client.post(
            reverse('facility-list'),
            data=feature,
            content_type='application/json',
        )
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        created = create_resp.json()
        facility_id = created.get('id')
        self.assertTrue(EmergencyFacility.objects.filter(pk=facility_id).exists())

        update_feature = {
            'type': 'Feature',
            'geometry': feature['geometry'],
            'properties': {
                'name': 'Updated Facility',
                'type': 'hospital',
                'address': 'Updated',
            },
        }
        update_resp = self.client.patch(
            reverse('facility-detail', args=[facility_id]),
            data=update_feature,
            content_type='application/json',
        )
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            EmergencyFacility.objects.get(pk=facility_id).name,
            'Updated Facility',
        )

        delete_resp = self.client.delete(
            reverse('facility-detail', args=[facility_id]),
        )
        self.assertEqual(delete_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(EmergencyFacility.objects.filter(pk=facility_id).exists())
