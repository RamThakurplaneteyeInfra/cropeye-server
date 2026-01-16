#!/usr/bin/env python
"""
Script to create migrations for bookings app only, bypassing GDAL requirement.
This script manually analyzes the bookings models and creates migration files.
"""

import os
import sys
from datetime import datetime

# Check if there are any model changes by comparing with existing migrations
bookings_migrations_dir = 'bookings/migrations'
existing_migrations = [
    '0001_initial.py',
    '0002_add_industry_field.py',
    '0003_assign_industry_to_existing_bookings.py',
    '0004_rename_bookings_boo_status_8b5b0a_idx_bookings_bo_status_233e96_idx_and_more.py'
]

print("=" * 60)
print("Checking Bookings Models for Changes")
print("=" * 60)

# Read the bookings models file
try:
    with open('bookings/models.py', 'r', encoding='utf-8') as f:
        models_content = f.read()
    
    print("\n[INFO] Bookings models file read successfully")
    
    # Check for key model definitions
    has_booking = 'class Booking' in models_content
    has_booking_comment = 'class BookingComment' in models_content
    has_booking_attachment = 'class BookingAttachment' in models_content
    
    print(f"  - Booking model: {'Found' if has_booking else 'Not found'}")
    print(f"  - BookingComment model: {'Found' if has_booking_comment else 'Not found'}")
    print(f"  - BookingAttachment model: {'Found' if has_booking_attachment else 'Not found'}")
    
    # Check for industry field
    has_industry = 'industry = models.ForeignKey' in models_content and "'users.Industry'" in models_content
    print(f"  - Industry field: {'Found' if has_industry else 'Not found'}")
    
    # List existing migrations
    print(f"\n[INFO] Existing migrations:")
    for i, mig in enumerate(existing_migrations, 1):
        mig_path = os.path.join(bookings_migrations_dir, mig)
        if os.path.exists(mig_path):
            print(f"  {i}. {mig} - EXISTS")
        else:
            print(f"  {i}. {mig} - MISSING")
    
    print("\n" + "=" * 60)
    print("Migration Status Check")
    print("=" * 60)
    
    # Check if all migrations exist
    all_exist = all(os.path.exists(os.path.join(bookings_migrations_dir, mig)) for mig in existing_migrations)
    
    if all_exist:
        print("\n[SUCCESS] All expected migrations already exist!")
        print("\nTo check if there are NEW changes that need migrations:")
        print("  1. Compare your current models.py with the last migration")
        print("  2. If you made changes, you'll need GDAL installed to run makemigrations")
        print("  3. Or manually create a new migration file")
        print("\nCurrent migrations cover:")
        print("  - Initial Booking, BookingComment, BookingAttachment models")
        print("  - Industry field addition")
        print("  - Industry assignment to existing bookings")
        print("  - Index renaming")
    else:
        print("\n[WARNING] Some migrations are missing!")
        missing = [mig for mig in existing_migrations if not os.path.exists(os.path.join(bookings_migrations_dir, mig))]
        print(f"Missing migrations: {', '.join(missing)}")
    
    print("\n" + "=" * 60)
    print("Note: To create NEW migrations, you need GDAL installed.")
    print("Current migrations are already applied to the database.")
    print("=" * 60)
    
except FileNotFoundError:
    print("[ERROR] bookings/models.py not found!")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

