#!/usr/bin/env python
"""
Direct PostgreSQL connection script to apply vendors migration.
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

def apply_migration():
    """Apply vendors migration directly to database"""
    
    print("=" * 60)
    print("Applying Vendors Migration (Direct Database Connection)".center(60))
    print("=" * 60)
    
    try:
        # Connect to database
        print(f"\nConnecting to database: {DB_CONFIG['dbname']}@{DB_CONFIG['host']}")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print("[OK] Connected successfully\n")
        
        # Check if migration already applied
        cur.execute("""
            SELECT COUNT(*) FROM django_migrations 
            WHERE app = 'vendors' AND name = '0003_add_gstin_state_city_fields'
        """)
        if cur.fetchone()[0] > 0:
            print("[INFO] Migration 0003_add_gstin_state_city_fields already applied")
            cur.close()
            conn.close()
            return True
        
        print("Applying migration: 0003_add_gstin_state_city_fields")
        print("-" * 60)
        
        # Add gstin_number field
        print("1. Adding gstin_number field...")
        try:
            cur.execute("""
                ALTER TABLE vendors_vendor 
                ADD COLUMN gstin_number VARCHAR(15) NULL;
            """)
            print("   [OK] gstin_number field added")
        except psycopg2.errors.DuplicateColumn:
            print("   [SKIP] gstin_number field already exists")
        
        # Add state field
        print("2. Adding state field...")
        try:
            cur.execute("""
                ALTER TABLE vendors_vendor 
                ADD COLUMN state VARCHAR(100) NULL;
            """)
            print("   [OK] state field added")
        except psycopg2.errors.DuplicateColumn:
            print("   [SKIP] state field already exists")
        
        # Add city field
        print("3. Adding city field...")
        try:
            cur.execute("""
                ALTER TABLE vendors_vendor 
                ADD COLUMN city VARCHAR(100) DEFAULT '' NOT NULL;
            """)
            print("   [OK] city field added")
        except psycopg2.errors.DuplicateColumn:
            print("   [SKIP] city field already exists")
        
        # Make contact_person nullable
        print("4. Making contact_person nullable...")
        try:
            cur.execute("""
                ALTER TABLE vendors_vendor 
                ALTER COLUMN contact_person DROP NOT NULL;
            """)
            print("   [OK] contact_person is now nullable")
        except psycopg2.errors.NotNullViolation:
            print("   [WARNING] Cannot make nullable - existing data has NULL values")
        except Exception as e:
            if 'does not exist' not in str(e):
                print(f"   [SKIP] {e}")
        
        # Add index for gstin_number
        print("5. Adding index for gstin_number...")
        try:
            cur.execute("""
                CREATE INDEX vendors_ven_gstin_n_123abc_idx 
                ON vendors_vendor (gstin_number);
            """)
            print("   [OK] Index created")
        except psycopg2.errors.DuplicateTable:
            print("   [SKIP] Index already exists")
        
        # Record migration in django_migrations table
        print("6. Recording migration in django_migrations...")
        cur.execute("""
            INSERT INTO django_migrations (app, name, applied)
            VALUES ('vendors', '0003_add_gstin_state_city_fields', %s)
            ON CONFLICT DO NOTHING;
        """, (datetime.now(),))
        print("   [OK] Migration recorded")
        
        # Commit all changes
        conn.commit()
        cur.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Vendors migration applied successfully!".center(60))
        print("=" * 60)
        return True
        
    except psycopg2.Error as e:
        print(f"\n[ERROR] Database error: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}")
        if 'conn' in locals():
            if conn:
                conn.rollback()
                conn.close()
        return False

if __name__ == "__main__":
    success = apply_migration()
    if not success:
        exit(1)

