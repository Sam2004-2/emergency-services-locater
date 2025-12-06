"""
User profile model with role-based access control.

Extends Django's built-in User model with a OneToOne relationship
to add role, badge number, and vehicle assignment for responders.
"""
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


ROLE_CHOICES = (
    ('admin', 'Administrator'),
    ('dispatcher', 'Dispatcher'),
    ('responder', 'Responder'),
    ('viewer', 'Viewer'),
)


class UserProfile(models.Model):
    """
    Extended user profile with role-based access control.

    Roles:
    - admin: Full access, can manage users and all operations
    - dispatcher: Can create incidents and dispatch vehicles/responders
    - responder: Can view assigned incidents and update their status
    - viewer: Read-only access to map and incidents
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='viewer',
        db_index=True
    )
    badge_number = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = 'accounts_userprofile'

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_dispatcher(self):
        """Check if user has dispatcher privileges (admin or dispatcher role)."""
        return self.role in ('admin', 'dispatcher')

    @property
    def is_responder(self):
        """Check if user is a responder."""
        return self.role == 'responder'

    @property
    def is_admin(self):
        """Check if user is an administrator."""
        return self.role == 'admin'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create a UserProfile when a new User is created."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Ensure UserProfile is saved when User is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
