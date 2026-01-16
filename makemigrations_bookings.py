#!/usr/bin/env python
"""
Script to run makemigrations for bookings app without GDAL requirement.
Temporarily switches database engine to regular PostgreSQL.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm_management.settings')

# Import settings before Django setup
from django.conf import settings

# Store original engine
original_engine = settings.DATABASES['default']['ENGINE']
print(f"Original database engine: {original_engine}")

# Temporarily use regular PostgreSQL (not PostGIS) to avoid GDAL requirement
settings.DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql'
print("Temporarily switched to regular PostgreSQL backend")

try:
    django.setup()
    
    from django.core.management import call_command
    from io import StringIO
    
    print("\n" + "=" * 60)
    print("Running makemigrations for bookings app...")
    print("=" * 60 + "\n")
    
    # Capture output
    out = StringIO()
    
    # Run makemigrations
    call_command('makemigrations', 'bookings', stdout=out, verbosity=2)
    
    output = out.getvalue()
    if output:
        print(output)
    else:
        print("No changes detected in bookings models.")
        print("All migrations are up to date.")
    
    print("\n" + "=" * 60)
    print("makemigrations completed successfully!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[ERROR] Error running makemigrations: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    # Restore original engine
    settings.DATABASES['default']['ENGINE'] = original_engine
    print(f"\nRestored database engine to: {original_engine}")

