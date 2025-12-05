from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from facilities.api import CountyViewSet, FacilityViewSet
from incidents.views import DashboardView, IncidentMapView, CoverageAnalysisView

router = DefaultRouter()
router.register(r'facilities', FacilityViewSet, basename='facility')
router.register(r'counties', CountyViewSet, basename='county')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/', include('incidents.urls')),  # Incident API endpoints
    path('accounts/', include('accounts.urls')),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('map/', IncidentMapView.as_view(), name='incident-map'),
    path('coverage/', CoverageAnalysisView.as_view(), name='coverage-analysis'),
    path('', include('frontend.urls')),
]
