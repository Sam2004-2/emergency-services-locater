"""
Data migration to create Editors and Viewers groups with appropriate permissions.

Editors: Can add, change, delete emergency facilities
Viewers: Read-only access (default for new registrations)
"""
from django.db import migrations


def create_groups(apps, schema_editor):
    """Create Editors and Viewers groups with permissions."""
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    
    # Create Viewers group (no special permissions - read-only via API)
    viewers_group, _ = Group.objects.get_or_create(name='Viewers')
    
    # Create Editors group with facility management permissions
    editors_group, _ = Group.objects.get_or_create(name='Editors')
    
    # Try to get EmergencyFacility content type and permissions
    try:
        # Get content type for EmergencyFacility
        facility_ct = ContentType.objects.get(
            app_label='services',
            model='emergencyfacility'
        )
        
        # Get permissions for EmergencyFacility
        facility_permissions = Permission.objects.filter(
            content_type=facility_ct,
            codename__in=['add_emergencyfacility', 'change_emergencyfacility', 'delete_emergencyfacility']
        )
        
        # Assign all facility permissions to Editors
        editors_group.permissions.set(facility_permissions)
        
    except ContentType.DoesNotExist:
        # ContentType doesn't exist yet - permissions will be assigned later
        pass


def remove_groups(apps, schema_editor):
    """Remove created groups (reverse migration)."""
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=['Editors', 'Viewers']).delete()


class Migration(migrations.Migration):
    """Create user groups for role-based access control."""
    
    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]
    
    operations = [
        migrations.RunPython(create_groups, remove_groups),
    ]
