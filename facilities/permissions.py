"""
Custom permission classes for role-based access control.

Implements group-based permissions following Django's built-in auth system.
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsEditorOrReadOnly(BasePermission):
    """
    Allow read access to everyone, write access only to Editors group.
    
    Members of the 'Editors' group can perform any action.
    All other users (including anonymous) have read-only access.
    
    Usage:
        permission_classes = [IsEditorOrReadOnly]
    """
    
    message = 'You must be an Editor to modify facilities.'
    
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in SAFE_METHODS:
            return True
        
        # Write permissions require authentication and Editors group
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers always have access
        if request.user.is_superuser:
            return True
        
        # Check for Editors group membership
        return request.user.groups.filter(name='Editors').exists()
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in SAFE_METHODS:
            return True
        
        # Write permissions handled by has_permission
        return self.has_permission(request, view)


class IsAdminOrReadOnly(BasePermission):
    """
    Allow read access to everyone, write access only to staff/superusers.
    
    Useful for admin-managed data like county boundaries.
    """
    
    message = 'Only administrators can modify this resource.'
    
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        
        return request.user and (request.user.is_staff or request.user.is_superuser)


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission to allow owners to edit their own objects.
    
    Assumes the model has a 'created_by' or 'owner' field.
    """
    
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        
        # Check for owner field
        owner_field = getattr(obj, 'created_by', None) or getattr(obj, 'owner', None)
        if owner_field:
            return owner_field == request.user
        
        return False
