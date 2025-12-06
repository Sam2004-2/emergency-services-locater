"""Admin configuration for user profiles."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile within User admin."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class UserAdmin(BaseUserAdmin):
    """Extended User admin with profile inline."""
    inlines = (UserProfileInline,)
    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'is_staff', 'get_role'
    )
    list_select_related = ('profile',)

    def get_role(self, instance):
        """Display user's role in the list."""
        if hasattr(instance, 'profile'):
            return instance.profile.get_role_display()
        return '-'
    get_role.short_description = 'Role'

    def get_inline_instances(self, request, obj=None):
        """Only show inline when editing existing user."""
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


# Re-register User admin with profile inline
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
