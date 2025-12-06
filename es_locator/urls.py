from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from accounts.urls import api_urlpatterns as accounts_api_urls
from boundaries.api import CountyViewSet
from services.api import FacilityViewSet

router = DefaultRouter()
router.register(r'facilities', FacilityViewSet, basename='facility')
router.register(r'counties', CountyViewSet, basename='county')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/', include(accounts_api_urls)),
    path('api/', include('incidents.urls')),
    path('accounts/', include('accounts.urls')),
    path('', include('frontend.urls')),
]
