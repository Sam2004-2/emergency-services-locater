"""URL configuration for accounts app."""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CurrentUserAPIView,
    CustomLoginView,
    CustomTokenObtainPairView,
    logout_to_home,
)

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    # Force logout to always redirect to home (no confirmation page)
    path('logout/', logout_to_home, name='logout'),
]

# API URLs (to be included under /api/)
api_urlpatterns = [
    path('auth/me/', CurrentUserAPIView.as_view(), name='current-user'),
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token-obtain'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
