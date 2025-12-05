"""
Views for the emergency services dashboard.
"""
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.utils import timezone

from .models import Incident, Vehicle


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Main dispatcher dashboard view.
    
    Displays:
    - Real-time map with incidents and vehicles
    - Incident list with filtering
    - Vehicle status summary
    - Quick dispatch controls
    """
    template_name = 'incidents/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Active incidents
        active_statuses = ['pending', 'dispatched', 'en_route', 'on_scene']
        active_incidents = Incident.objects.filter(
            status__in=active_statuses
        )
        
        # Incident counts by status
        incident_counts = Incident.objects.filter(
            status__in=active_statuses
        ).values('status').annotate(count=Count('id'))
        
        status_counts = {item['status']: item['count'] for item in incident_counts}
        
        # Priority breakdown
        priority_counts = Incident.objects.filter(
            status__in=active_statuses
        ).values('priority').annotate(count=Count('id'))
        
        priority_breakdown = {item['priority']: item['count'] for item in priority_counts}
        
        # Vehicle summary
        vehicles = Vehicle.objects.all()
        vehicle_summary = vehicles.values('status').annotate(count=Count('id'))
        vehicle_counts = {item['status']: item['count'] for item in vehicle_summary}
        
        # Recent incidents (last 24 hours)
        yesterday = timezone.now() - timezone.timedelta(days=1)
        recent_incidents = Incident.objects.filter(
            created_at__gte=yesterday
        ).count()
        
        context.update({
            'active_incidents': active_incidents,
            'pending_count': status_counts.get('pending', 0),
            'dispatched_count': status_counts.get('dispatched', 0),
            'en_route_count': status_counts.get('en_route', 0),
            'on_scene_count': status_counts.get('on_scene', 0),
            'priority_breakdown': priority_breakdown,
            'vehicle_counts': vehicle_counts,
            'available_vehicles': vehicle_counts.get('available', 0),
            'total_vehicles': vehicles.count(),
            'recent_incidents': recent_incidents,
        })
        
        return context


class IncidentMapView(LoginRequiredMixin, TemplateView):
    """
    Full-screen map view for incident visualization.
    """
    template_name = 'incidents/map.html'


class CoverageAnalysisView(LoginRequiredMixin, TemplateView):
    """
    Coverage analysis view with gap identification.
    """
    template_name = 'incidents/coverage.html'
