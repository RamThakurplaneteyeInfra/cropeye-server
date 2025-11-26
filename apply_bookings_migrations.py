#!/usr/bin/env python
"""
Script to apply bookings migrations without requiring GDAL.
This bypasses Django's normal migration system by using raw SQL.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm_management.settings')

# Temporarily change database engine to avoid GDAL requirement
import django.conf
from django.conf import settings

# Store original engine
original_engine = settings.DATABASES['default']['ENGINE']

# Temporarily use regular PostgreSQL (not PostGIS)
settings.DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql'

try:
    django.setup()
    
    from django.db import connection
    
    print("=" * 60)
    print("Applying Bookings Migrations")
    print("=" * 60)
    
    with connection.cursor() as cursor:
        # Migration 0002: Add industry field
        print("\n[1/3] Checking industry field...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'bookings_booking' 
            AND column_name = 'industry_id'
        """)
        
        if not cursor.fetchone():
            print("   → Adding industry_id column...")
            cursor.execute("""
                ALTER TABLE bookings_booking 
                ADD COLUMN industry_id INTEGER NULL
            """)
            
            cursor.execute("""
                ALTER TABLE bookings_booking 
                ADD CONSTRAINT bookings_booking_industry_id_fkey 
                FOREIGN KEY (industry_id) 
                REFERENCES users_industry(id) 
                ON DELETE CASCADE
            """)
            print("   ✅ Industry field added")
        else:
            print("   ✅ Industry field already exists")
        
        # Migration 0003: Assign industry to existing bookings
        print("\n[2/3] Assigning industry to existing bookings...")
        cursor.execute("""
            UPDATE bookings_booking 
            SET industry_id = (
                SELECT industry_id 
                FROM users_user 
                WHERE users_user.id = bookings_booking.created_by_id
            )
            WHERE industry_id IS NULL 
            AND created_by_id IS NOT NULL
        """)
        updated_count = cursor.rowcount
        print(f"   ✅ Updated {updated_count} bookings with industry")
        
        # Migration 0004: Rename indexes
        print("\n[3/3] Renaming indexes...")
        index_renames = [
            ('bookings_boo_status_8b5b0a_idx', 'bookings_bo_status_233e96_idx'),
            ('bookings_boo_bookin_0b4b5a_idx', 'bookings_bo_booking_3ec655_idx'),
            ('bookings_boo_start_d_0b4b5a_idx', 'bookings_bo_start_d_3e8155_idx'),
            ('bookings_boo_end_dat_0b4b5a_idx', 'bookings_bo_end_dat_f79cb7_idx'),
        ]
        
        for old_name, new_name in index_renames:
            cursor.execute("""
                SELECT 1 FROM pg_indexes 
                WHERE indexname = %s
            """, [old_name])
            
            if cursor.fetchone():
                cursor.execute(f'ALTER INDEX "{old_name}" RENAME TO "{new_name}"')
                print(f"   ✅ Renamed {old_name} → {new_name}")
            else:
                print(f"   ⏭️  Index {old_name} not found (may already be renamed)")
        
        # Mark migrations as applied in django_migrations table
        print("\n[4/4] Marking migrations as applied...")
        migrations_to_mark = [
            ('bookings', '0002_add_industry_field'),
            ('bookings', '0003_assign_industry_to_existing_bookings'),
            ('bookings', '0004_rename_bookings_boo_status_8b5b0a_idx_bookings_bo_status_233e96_idx_and_more'),
        ]
        
        for app, migration in migrations_to_mark:
            cursor.execute("""
                SELECT 1 FROM django_migrations 
                WHERE app = %s AND name = %s
            """, [app, migration])
            
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied)
                    VALUES (%s, %s, NOW())
                """, [app, migration])
                print(f"   ✅ Marked {app}.{migration} as applied")
            else:
                print(f"   ⏭️  {app}.{migration} already marked as applied")
        
        connection.commit()
    
    print("\n" + "=" * 60)
    print("✅ All bookings migrations applied successfully!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    # Restore original engine
    settings.DATABASES['default']['ENGINE'] = original_engine

