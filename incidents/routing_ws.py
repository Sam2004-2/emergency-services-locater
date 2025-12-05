"""
WebSocket URL routing for incidents app.
"""
from django.urls import re_path
from . import consumers


websocket_urlpatterns = [
    re_path(r'ws/incidents/$', consumers.IncidentConsumer.as_asgi()),
    re_path(r'ws/vehicles/$', consumers.VehicleConsumer.as_asgi()),
    re_path(r'ws/dispatch/$', consumers.DispatchConsumer.as_asgi()),
]
