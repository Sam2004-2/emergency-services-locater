"""
Authentication views and API endpoints.

Provides login/logout views and an API endpoint for retrieving
the current user's information and role.
"""
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class CustomLoginView(LoginView):
    """
    Custom login view that redirects based on user role.

    - Dispatchers/Admins -> Dashboard
    - Responders -> Dashboard
    - Viewers -> Map
    """
    template_name = 'frontend/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if hasattr(user, 'profile'):
            if user.profile.is_dispatcher or user.profile.is_responder:
                return reverse_lazy('dashboard')
        return reverse_lazy('home')


class CustomLogoutView(LogoutView):
    """Logout view that redirects to home page."""
    next_page = reverse_lazy('home')


class CurrentUserAPIView(APIView):
    """
    API endpoint returning current user info and role.

    GET /api/auth/me/
    Returns: {
        authenticated: boolean,
        user: {id, username, email, first_name, last_name},
        role: string,
        is_dispatcher: boolean,
        is_responder: boolean,
        is_admin: boolean
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = getattr(request.user, 'profile', None)
        return Response({
            'authenticated': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
            },
            'role': profile.role if profile else 'viewer',
            'role_display': profile.get_role_display() if profile else 'Viewer',
            'is_dispatcher': profile.is_dispatcher if profile else False,
            'is_responder': profile.is_responder if profile else False,
            'is_admin': profile.is_admin if profile else False,
            'badge_number': profile.badge_number if profile else '',
        })
