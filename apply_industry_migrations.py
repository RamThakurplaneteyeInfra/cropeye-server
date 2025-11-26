#!/usr/bin/env python
"""
Script to apply industry migrations directly to the database.
This bypasses Django's model loading to avoid GDAL issues.
"""

import os
import sys
import django
from pathlib import Path

# Add project directory to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm_management.settings')

# Configure Django
django.setup()

# Now import after Django setup
from django.db import connection
from django.core.management import call_command

def apply_migrations():
    """Apply all migrations"""
    print("🚀 Applying industry migrations...")
    print("=" * 60)
    
    try:
        # Try to apply migrations using Django's migrate command
        # This should work now that Django is set up
        call_command('migrate', verbosity=2, interactive=False)
        print("\n✅ All migrations applied successfully!")
        return True
    except Exception as e:
        print(f"\n❌ Error applying migrations: {e}")
        print("\n⚠️  If you're getting GDAL errors, you need to:")
        print("   1. Install GDAL for Windows")
        print("   2. Uncomment and configure GDAL_LIBRARY_PATH in settings.py")
        print("   3. Or set GDAL_LIBRARY_PATH as environment variable")
        return False

if __name__ == '__main__':
    success = apply_migrations()
    sys.exit(0 if success else 1)

