from django.urls import path

from .views import DashboardView, MapView

urlpatterns = [
    path('', MapView.as_view(), name='home'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]
