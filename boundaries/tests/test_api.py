from django.urls import reverse
from rest_framework import status

from core.tests.base import SpatialAPITestCase


class CountyAPITests(SpatialAPITestCase):
    def test_county_list_geojson(self):
        resp = self.client.get(reverse('county-list'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        features = self.unwrap_features(resp.json())
        self.assertGreaterEqual(len(features), 1)
        self.assertIn('geometry', features[0])

    def test_county_detail(self):
        resp = self.client.get(reverse('county-detail', args=[self.county.id]))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data.get('id'), self.county.id)
        self.assertEqual(data.get('properties', {}).get('name_en'), 'Dublin')
