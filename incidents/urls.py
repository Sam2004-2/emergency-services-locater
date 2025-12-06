"""URL configuration for incidents API."""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .api import DispatchViewSet, IncidentViewSet, VehicleViewSet

router = DefaultRouter()
router.register(r'incidents', IncidentViewSet, basename='incident')
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'dispatches', DispatchViewSet, basename='dispatch')

urlpatterns = router.urls
