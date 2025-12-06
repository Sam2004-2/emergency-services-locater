"""URL configuration for accounts app."""
from django.urls import path

from .views import CurrentUserAPIView, CustomLoginView, CustomLogoutView

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
]

# API URLs (to be included under /api/)
api_urlpatterns = [
    path('auth/me/', CurrentUserAPIView.as_view(), name='current-user'),
]
