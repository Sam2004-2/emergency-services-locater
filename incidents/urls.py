"""
URL routing for incidents app REST API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api import IncidentViewSet, VehicleViewSet, RoutingViewSet, CoverageViewSet


router = DefaultRouter()
router.register(r'incidents', IncidentViewSet, basename='incident')
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'routing', RoutingViewSet, basename='routing')
router.register(r'coverage', CoverageViewSet, basename='coverage')

urlpatterns = [
    path('', include(router.urls)),
]
