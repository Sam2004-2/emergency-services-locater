# Django Migrations Guide

## ✅ Your Database is Now Django-Managed!

Your database has been successfully converted from SQL scripts to Django migrations. This provides better version control, easier deployments, and automatic schema management.

---

## What Changed?

### Before (SQL Scripts)
- Tables created manually via SQL scripts in `db/schema/`
- Models had `managed = False`
- Schema changes required manual SQL
- No migration history

### After (Django Migrations)
- ✅ Tables managed by Django migrations
- ✅ Full migration history tracked
- ✅ Schema changes via `makemigrations` and `migrate`
- ✅ Automatic spatial indexes
- ✅ Better field validation

---

## New Database Schema

### Tables

#### `services_emergencyfacility`
```python
- id (BigAutoField, PK, auto-increment)
- name (CharField, max 200)
- type (CharField, max 32, indexed)
- address (CharField, max 500, optional)
- phone (CharField, max 50, optional)  
- website (URLField, max 500, optional, validated)
- properties (JSONField, default {})
- geom (PointField, SRID 4326, spatial index)
- created_at (DateTimeField, auto-added)
- updated_at (DateTimeField, auto-updated)

Indexes:
- type + created_at composite index
- GIST spatial index on geom
```

#### `boundaries_county`
```python
- id (BigAutoField, PK, auto-increment)
- source_id (CharField, max 100, optional)
- name_en (CharField, max 100, indexed)
- name_local (CharField, max 100, optional)
- iso_code (CharField, max 10, unique, optional)
- geom (MultiPolygonField, SRID 4326, spatial index)

Indexes:
- name_en index
- iso_code unique index
- GIST spatial index on geom
```

---

## Migration Files

### Boundaries App
1. **`0001_initial.py`** - Initial County model (from old SQL schema)
2. **`0002_alter_county_options.py`** - Updated Meta options
3. **`0003_alter_county_geom_alter_county_id_and_more.py`** - Django-managed fields

### Services App
1. **`0001_initial.py`** - Initial EmergencyFacility model (from old SQL schema)
2. **`0002_alter_emergencyfacility_options.py`** - Updated Meta options
3. **`0003_alter_emergencyfacility_address_and_more.py`** - Django-managed fields

---

## How to Use Django Migrations

### Making Schema Changes

1. **Edit your model** (e.g., add a field):
```python
# services/models.py
class EmergencyFacility(models.Model):
    # ... existing fields ...
    operating_hours = models.CharField(max_length=100, blank=True)  # NEW
```

2. **Generate migration**:
```bash
# Local
python manage.py makemigrations

# Docker
docker-compose exec web python manage.py makemigrations
```

3. **Review the migration** (in `services/migrations/000X_...py`)

4. **Apply migration**:
```bash
# Local
python manage.py migrate

# Docker
docker-compose exec web python manage.py migrate
```

5. **Commit migration file to Git**:
```bash
git add services/migrations/000X_*.py
git commit -m "Add operating_hours field to EmergencyFacility"
git push
```

### Common Migration Commands

```bash
# Show migration status
python manage.py showmigrations

# Show SQL for a migration (without running it)
python manage.py sqlmigrate services 0003

# Rollback to a specific migration
python manage.py migrate services 0002

# Rollback all migrations for an app
python manage.py migrate services zero

# Show unapplied migrations
python manage.py showmigrations --plan

# Fake a migration (mark as applied without running)
python manage.py migrate services 0003 --fake
```

---

## Deployment Workflow

### New Deployment

1. **Clone repository**
2. **Start containers**:
```bash
docker-compose up -d
```

3. **Run migrations**:
```bash
docker-compose exec web python manage.py migrate
```

4. **Import data** (if needed):
```bash
docker-compose exec web python manage.py import_counties
docker-compose exec web python manage.py import_facilities
```

### Updating Existing Deployment

1. **Pull latest code**:
```bash
git pull origin main
```

2. **Apply new migrations**:
```bash
docker-compose exec web python manage.py migrate
```

3. **Restart services** (if needed):
```bash
docker-compose restart web nginx
```

---

## Benefits of Django Migrations

### ✅ Version Control
- Every schema change is tracked in Git
- Easy to see what changed and when
- Can rollback to any previous version

### ✅ Team Collaboration
- Migrations are shared via Git
- Everyone gets the same database schema
- No manual SQL script coordination

### ✅ Automatic Spatial Indexes
- `spatial_index=True` on geometry fields
- Django creates GIST indexes automatically
- Optimal for PostGIS queries

### ✅ Field Validation
- URLField validates URLs
- CharField enforces max_length
- Choices enforce valid values
- Better data integrity

### ✅ Timestamps
- `auto_now_add` for creation time
- `auto_now` for update time
- No manual timestamp management

### ✅ Easier Deployments
- One command: `migrate`
- Automatic dependency resolution
- Safe rollback mechanism

---

## Troubleshooting

### Migration Conflicts

If you get migration conflicts:

```bash
# Show conflicting migrations
python manage.py showmigrations

# Option 1: Merge migrations
python manage.py makemigrations --merge

# Option 2: Rollback and reapply
python manage.py migrate services 0002
python manage.py migrate services
```

### Reset Migrations (Development Only)

**⚠️ WARNING: This will delete all data!**

```bash
# Drop database
docker-compose exec db psql -U postgres -c "DROP DATABASE es_locator;"
docker-compose exec db psql -U postgres -c "CREATE DATABASE es_locator;"
docker-compose exec db psql -U postgres -d es_locator -c "CREATE EXTENSION postgis;"

# Delete migration history
docker-compose exec web python manage.py migrate --fake services zero
docker-compose exec web python manage.py migrate --fake boundaries zero

# Recreate from scratch
docker-compose exec web python manage.py migrate
```

### Check Migration SQL

Before applying a migration, see what SQL it will run:

```bash
python manage.py sqlmigrate services 0003
```

### Fake Migrations

If tables already exist (e.g., from manual SQL), fake the migration:

```bash
python manage.py migrate services 0003 --fake
```

---

## Data Migration Script

A data migration script (`migrate_to_django.py`) is provided to help transition from old SQL-managed tables to new Django-managed tables.

**⚠️ Use with caution in production - always backup first!**

```bash
# Backup first!
docker-compose exec db pg_dump -U postgres es_locator > backup.sql

# Run migration script
docker-compose exec web python migrate_to_django.py
```

The script:
1. Backs up data from old tables
2. Drops old tables
3. Creates new Django-managed tables
4. Restores data

---

## Best Practices

### ✅ DO

- Commit migration files to Git
- Review migrations before applying
- Test migrations in development first
- Keep migrations small and focused
- Run migrations as part of deployment
- Backup before major migrations

### ❌ DON'T

- Edit applied migration files
- Delete migration files
- Skip migrations in deployment
- Manually modify tables Django manages
- Share databases between environments

---

## Summary

Your database is now fully managed by Django with:

✅ **5 migration files** tracking all schema changes  
✅ **Spatial indexes** automatically created  
✅ **Better field types** with validation  
✅ **Auto-timestamps** on records  
✅ **Composite indexes** for performance  
✅ **Version-controlled schema** in Git  

**Next steps**: Make schema changes via models + migrations, never manual SQL!

---

## Questions?

See:
- [Django Migrations Docs](https://docs.djangoproject.com/en/5.0/topics/migrations/)
- [GeoDjango Docs](https://docs.djangoproject.com/en/5.0/ref/contrib/gis/)
- `docs/DATABASE_SCHEMA.md` for current schema reference
