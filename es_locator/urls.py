from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from accounts.urls import api_urlpatterns as accounts_api_urls
from accounts.views import CustomLogoutView, logout_to_home
from boundaries.api import CountyViewSet
from services.api import FacilityViewSet

router = DefaultRouter()
router.register(r'facilities', FacilityViewSet, basename='facility')
router.register(r'counties', CountyViewSet, basename='county')

urlpatterns = [
    # Force admin logout to use our redirect-to-home view (avoids admin login redirect)
    path('admin/logout/', logout_to_home, name='admin-logout'),
    path('admin/', admin.site.urls),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path('api/', include(router.urls)),
    path('api/', include(accounts_api_urls)),
    path('api/', include('incidents.urls')),
    path('accounts/', include('accounts.urls')),
    path('', include('frontend.urls')),
]
