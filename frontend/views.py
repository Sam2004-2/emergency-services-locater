from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class MapView(TemplateView):
    template_name = 'frontend/map.html'


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'frontend/dashboard.html'
    login_url = '/accounts/login/'
