#!/usr/bin/env python
"""
Direct PostgreSQL connection script to apply bookings migrations.
This bypasses Django completely to avoid GDAL requirement.
"""

import psycopg2
import os
from datetime import datetime

# Database connection settings (from environment or defaults)
DB_CONFIG = {
    'dbname': os.environ.get('DB_NAME', 'neoce'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'admin'),
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
}

def apply_migrations():
    """Apply bookings migrations directly to database"""
    
    print("=" * 60)
    print("Applying Bookings Migrations (Direct Database Connection)")
    print("=" * 60)
    
    try:
        # Connect to database
        print(f"\nConnecting to database: {DB_CONFIG['dbname']}@{DB_CONFIG['host']}")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("   [OK] Connected successfully")
        
        # Migration 0002: Add industry field
        print("\n[1/4] Checking industry field...")
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
            print("   [OK] Industry field added")
        else:
            print("   [OK] Industry field already exists")
        
        # Migration 0003: Assign industry to existing bookings
        print("\n[2/4] Assigning industry to existing bookings...")
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
        print(f"   [OK] Updated {updated_count} bookings with industry")
        
        # Migration 0004: Rename indexes
        print("\n[3/4] Renaming indexes...")
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
            """, (old_name,))
            
            if cursor.fetchone():
                cursor.execute(f'ALTER INDEX "{old_name}" RENAME TO "{new_name}"')
                print(f"   [OK] Renamed {old_name} -> {new_name}")
            else:
                print(f"   [SKIP] Index {old_name} not found (may already be renamed)")
        
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
            """, (app, migration))
            
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied)
                    VALUES (%s, %s, %s)
                """, (app, migration, datetime.now()))
                print(f"   [OK] Marked {app}.{migration} as applied")
            else:
                print(f"   [SKIP] {app}.{migration} already marked as applied")
        
        # Commit all changes
        conn.commit()
        
        print("\n" + "=" * 60)
        print("[SUCCESS] All bookings migrations applied successfully!")
        print("=" * 60)
        
        # Close connection
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"\n[ERROR] Database Error: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = apply_migrations()
    exit(0 if success else 1)

