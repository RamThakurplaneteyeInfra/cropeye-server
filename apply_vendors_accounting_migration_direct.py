#!/usr/bin/env python
"""
Direct PostgreSQL connection script to apply vendors accounting migration.
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
    """Apply vendors accounting migration directly to database"""
    
    print("=" * 60)
    print("Applying Vendors Accounting Migration (Direct Database Connection)".center(60))
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
            WHERE app = 'vendors' AND name = '0004_add_accounting_fields'
        """)
        if cur.fetchone()[0] > 0:
            print("[INFO] Migration 0004_add_accounting_fields already applied")
            cur.close()
            conn.close()
            return True
        
        print("Applying migration: 0004_add_accounting_fields")
        print("-" * 60)
        
        # Add invoice_date field to PurchaseOrder
        print("1. Adding invoice_date field to PurchaseOrder...")
        try:
            cur.execute("""
                ALTER TABLE vendors_purchaseorder 
                ADD COLUMN invoice_date DATE NULL;
            """)
            print("   [OK] invoice_date field added")
        except psycopg2.errors.DuplicateColumn:
            print("   [SKIP] invoice_date field already exists")
        
        # Add invoice_number field to PurchaseOrder
        print("2. Adding invoice_number field to PurchaseOrder...")
        try:
            cur.execute("""
                ALTER TABLE vendors_purchaseorder 
                ADD COLUMN invoice_number VARCHAR(100) NULL;
            """)
            print("   [OK] invoice_number field added")
        except psycopg2.errors.DuplicateColumn:
            print("   [SKIP] invoice_number field already exists")
        
        # Add state field to PurchaseOrder
        print("3. Adding state field to PurchaseOrder...")
        try:
            cur.execute("""
                ALTER TABLE vendors_purchaseorder 
                ADD COLUMN state VARCHAR(100) NULL;
            """)
            print("   [OK] state field added")
        except psycopg2.errors.DuplicateColumn:
            print("   [SKIP] state field already exists")
        
        # Make inventory_item nullable in PurchaseOrderItem
        print("4. Making inventory_item nullable in PurchaseOrderItem...")
        try:
            cur.execute("""
                ALTER TABLE vendors_purchaseorderitem 
                ALTER COLUMN inventory_item_id DROP NOT NULL;
            """)
            print("   [OK] inventory_item is now nullable")
        except Exception as e:
            if 'does not exist' not in str(e):
                print(f"   [SKIP] {e}")
        
        # Add item_name field to PurchaseOrderItem
        print("5. Adding item_name field to PurchaseOrderItem...")
        try:
            cur.execute("""
                ALTER TABLE vendors_purchaseorderitem 
                ADD COLUMN item_name VARCHAR(200) DEFAULT '' NOT NULL;
            """)
            print("   [OK] item_name field added")
        except psycopg2.errors.DuplicateColumn:
            print("   [SKIP] item_name field already exists")
        
        # Add year_of_make field to PurchaseOrderItem
        print("6. Adding year_of_make field to PurchaseOrderItem...")
        try:
            cur.execute("""
                ALTER TABLE vendors_purchaseorderitem 
                ADD COLUMN year_of_make VARCHAR(10) NULL;
            """)
            print("   [OK] year_of_make field added")
        except psycopg2.errors.DuplicateColumn:
            print("   [SKIP] year_of_make field already exists")
        
        # Add estimate_cost field to PurchaseOrderItem
        print("7. Adding estimate_cost field to PurchaseOrderItem...")
        try:
            cur.execute("""
                ALTER TABLE vendors_purchaseorderitem 
                ADD COLUMN estimate_cost NUMERIC(12, 2) NULL;
            """)
            print("   [OK] estimate_cost field added")
        except psycopg2.errors.DuplicateColumn:
            print("   [SKIP] estimate_cost field already exists")
        
        # Add remark field to PurchaseOrderItem
        print("8. Adding remark field to PurchaseOrderItem...")
        try:
            cur.execute("""
                ALTER TABLE vendors_purchaseorderitem 
                ADD COLUMN remark TEXT DEFAULT '' NOT NULL;
            """)
            print("   [OK] remark field added")
        except psycopg2.errors.DuplicateColumn:
            print("   [SKIP] remark field already exists")
        
        # Make quantity have default value
        print("9. Setting default value for quantity...")
        try:
            cur.execute("""
                ALTER TABLE vendors_purchaseorderitem 
                ALTER COLUMN quantity SET DEFAULT 1;
            """)
            print("   [OK] quantity default set")
        except Exception as e:
            print(f"   [SKIP] {e}")
        
        # Make unit_price nullable
        print("10. Making unit_price nullable...")
        try:
            cur.execute("""
                ALTER TABLE vendors_purchaseorderitem 
                ALTER COLUMN unit_price DROP NOT NULL;
            """)
            print("   [OK] unit_price is now nullable")
        except Exception as e:
            if 'does not exist' not in str(e):
                print(f"   [SKIP] {e}")
        
        # Record migration in django_migrations table
        print("11. Recording migration in django_migrations...")
        cur.execute("""
            INSERT INTO django_migrations (app, name, applied)
            VALUES ('vendors', '0004_add_accounting_fields', %s)
            ON CONFLICT DO NOTHING;
        """, (datetime.now(),))
        print("   [OK] Migration recorded")
        
        # Commit all changes
        conn.commit()
        cur.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Vendors accounting migration applied successfully!".center(60))
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

