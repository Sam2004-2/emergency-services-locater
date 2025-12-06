"""
DRF permission classes for role-based access control.

These permissions check the user's profile role to determine access levels
for incident management operations.
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsDispatcher(BasePermission):
    """
    Allow access only to users with dispatcher or admin role.

    Dispatchers can:
    - Create incidents
    - Assign vehicles and responders
    - Update incident details
    """
    message = "You must be a dispatcher to perform this action."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'profile'):
            return False
        return request.user.profile.is_dispatcher


class IsResponder(BasePermission):
    """
    Allow access only to users with responder role.

    Responders can:
    - View their assigned incidents
    - Update status of assigned incidents
    """
    message = "You must be a responder to perform this action."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'profile'):
            return False
        return request.user.profile.is_responder


class IsDispatcherOrReadOnly(BasePermission):
    """
    Allow read access to any authenticated user.
    Write access only for dispatchers.

    Used for incident list/detail views where anyone can view
    but only dispatchers can create/modify.
    """
    message = "Write access requires dispatcher privileges."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        if not hasattr(request.user, 'profile'):
            return False
        return request.user.profile.is_dispatcher


class IsAssignedResponderOrDispatcher(BasePermission):
    """
    Allow access to the responder assigned to an incident,
    or any dispatcher.

    Used for incident status updates where only the assigned
    responder or a dispatcher can modify.
    """
    message = "You must be assigned to this incident or be a dispatcher."

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        profile = getattr(request.user, 'profile', None)
        if profile and profile.is_dispatcher:
            return True

        # Check if user is assigned responder
        if hasattr(obj, 'assigned_responder'):
            return obj.assigned_responder == request.user
        if hasattr(obj, 'responder'):
            return obj.responder == request.user

        return False


class IsAdminUser(BasePermission):
    """
    Allow access only to admin users.

    Admins have full access to all operations including
    user management.
    """
    message = "Administrator access required."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if not hasattr(request.user, 'profile'):
            return False
        return request.user.profile.is_admin
