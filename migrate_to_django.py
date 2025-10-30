#!/usr/bin/env python
"""
Migration script to convert from SQL-managed tables to Django-managed tables.

This script:
1. Backs up data from old tables
2. Drops old tables
3. Creates new Django-managed tables via migrations
4. Restores data to new tables
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'es_locator.settings')
django.setup()

from django.db import connection
from services.models import EmergencyFacility
from boundaries.models import County


def backup_data():
    """Backup data from existing tables."""
    print("📦 Backing up data...")
    
    with connection.cursor() as cursor:
        # Backup emergency facilities
        cursor.execute("""
            SELECT id, name, type, address, phone, website, properties, 
                   ST_AsText(geom), created_at, updated_at
            FROM emergency_facility
        """)
        facilities_data = cursor.fetchall()
        
        # Backup counties
        cursor.execute("""
            SELECT id, source_id, name_en, name_local, iso_code, ST_AsText(geom)
            FROM admin_counties
        """)
        counties_data = cursor.fetchall()
    
    print(f"✅ Backed up {len(facilities_data)} facilities and {len(counties_data)} counties")
    return facilities_data, counties_data


def drop_old_tables():
    """Drop old SQL-managed tables."""
    print("🗑️  Dropping old tables...")
    
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS emergency_facility CASCADE")
        cursor.execute("DROP TABLE IF EXISTS admin_counties CASCADE")
    
    print("✅ Old tables dropped")


def create_new_tables():
    """Create new Django-managed tables."""
    print("🏗️  Creating new Django-managed tables...")
    
    from django.core.management import call_command
    
    # Remove old migration records
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM django_migrations WHERE app IN ('services', 'boundaries')")
    
    # Run migrations to create new tables
    call_command('migrate', 'boundaries', '--fake-initial')
    call_command('migrate', 'services', '--fake-initial')
    
    print("✅ New tables created")


def restore_data(facilities_data, counties_data):
    """Restore data to new Django-managed tables."""
    print("📥 Restoring data...")
    
    from django.contrib.gis.geos import GEOSGeometry
    from datetime import datetime
    
    # Restore counties first (no dependencies)
    for row in counties_data:
        County.objects.create(
            id=row[0],
            source_id=row[1],
            name_en=row[2],
            name_local=row[3],
            iso_code=row[4],
            geom=GEOSGeometry(row[5], srid=4326)
        )
    
    # Restore facilities
    for row in facilities_data:
        EmergencyFacility.objects.create(
            id=row[0],
            name=row[1],
            type=row[2],
            address=row[3],
            phone=row[4],
            website=row[5],
            properties=row[6] or {},
            geom=GEOSGeometry(row[7], srid=4326),
            created_at=row[8] or datetime.now(),
            updated_at=row[9] or datetime.now()
        )
    
    print(f"✅ Restored {len(facilities_data)} facilities and {len(counties_data)} counties")


def main():
    """Run the migration process."""
    print("=" * 60)
    print("🔄 MIGRATING TO DJANGO-MANAGED DATABASE")
    print("=" * 60)
    
    try:
        # Step 1: Backup
        facilities_data, counties_data = backup_data()
        
        # Step 2: Drop old tables
        drop_old_tables()
        
        # Step 3: Create new tables
        create_new_tables()
        
        # Step 4: Restore data
        restore_data(facilities_data, counties_data)
        
        print("\n" + "=" * 60)
        print("✅ MIGRATION COMPLETE!")
        print("=" * 60)
        print("\n📊 Summary:")
        print(f"   - Counties: {County.objects.count()}")
        print(f"   - Emergency Facilities: {EmergencyFacility.objects.count()}")
        print("\n✨ Your database is now Django-managed!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\n⚠️  Migration failed. Please restore from backup if needed.")
        raise


if __name__ == '__main__':
    main()
