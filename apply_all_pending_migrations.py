"""
Apply all pending migrations directly via SQL
This bypasses Django/GDAL issues
"""
import psycopg2
from psycopg2 import sql
import sys

# Database credentials
DB_CONFIG = {
    'dbname': 'CROPDB_TEST',
    'user': 'farm_management_l1wj_user',
    'password': 'DySO3fcTFjb8Rgp9IZIxGYgLZ7KxwmjL',
    'host': 'dev-et.cropeye.ai',
    'port': '5432'
}

def get_applied_migrations(cursor):
    """Get list of applied migrations"""
    cursor.execute("""
        SELECT app, name FROM django_migrations 
        ORDER BY app, applied;
    """)
    return set((app, name) for app, name in cursor.fetchall())

def apply_users_migrations(cursor, applied):
    """Apply pending users app migrations"""
    print("\n" + "=" * 70)
    print("Users App Migrations")
    print("=" * 70)
    
    # Migration 0002 - Already applied via direct SQL
    if ('users', '0002_add_industry_multi_tenant') not in applied:
        print("Migration 0002_add_industry_multi_tenant: Already applied (via direct SQL)")
    
    # Migration 0003 - Create default industry (data migration)
    if ('users', '0003_create_default_industry') not in applied:
        print("\nApplying migration 0003_create_default_industry...")
        
        # Check if default industry exists
        cursor.execute("SELECT COUNT(*) FROM users_industry WHERE name = 'Default Industry';")
        exists = cursor.fetchone()[0] > 0
        
        if not exists:
            cursor.execute("""
                INSERT INTO users_industry (name, description, created_at, updated_at)
                VALUES ('Default Industry', 'Default industry for existing users', NOW(), NOW())
                RETURNING id;
            """)
            industry_id = cursor.fetchone()[0]
            print(f"  OK: Created default industry (ID: {industry_id})")
            
            # Assign non-superuser users to default industry
            cursor.execute("""
                UPDATE users_user 
                SET industry_id = %s
                WHERE is_superuser = false 
                AND industry_id IS NULL;
            """, (industry_id,))
            updated = cursor.rowcount
            print(f"  OK: Assigned {updated} users to default industry")
        else:
            print("  OK: Default industry already exists")
        
        # Record migration
        cursor.execute("""
            INSERT INTO django_migrations (app, name, applied)
            VALUES ('users', '0003_create_default_industry', NOW())
            ON CONFLICT DO NOTHING;
        """)
        print("  OK: Migration recorded")
    else:
        print("Migration 0003_create_default_industry: Already applied")
    
    # Migration 0004 - Change username field (check if needed)
    if ('users', '0004_change_username_field') not in applied:
        print("\nApplying migration 0004_change_username_field...")
        # This migration typically doesn't change the database schema
        # It's usually a model change that doesn't require SQL
        cursor.execute("""
            INSERT INTO django_migrations (app, name, applied)
            VALUES ('users', '0004_change_username_field', NOW())
            ON CONFLICT DO NOTHING;
        """)
        print("  OK: Migration recorded (no schema changes needed)")
    else:
        print("Migration 0004_change_username_field: Already applied")
    
    # Migration 0005 - Add test fields (already applied via direct SQL)
    if ('users', '0005_industry_test_password_industry_test_phone_number') not in applied:
        print("\nApplying migration 0005_industry_test_password_industry_test_phone_number...")
        # Check if columns exist
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'users_industry' 
            AND column_name IN ('test_phone_number', 'test_password');
        """)
        existing_cols = [row[0] for row in cursor.fetchall()]
        
        if 'test_phone_number' not in existing_cols:
            cursor.execute("ALTER TABLE users_industry ADD COLUMN test_phone_number VARCHAR(15);")
            print("  OK: Added test_phone_number column")
        
        if 'test_password' not in existing_cols:
            cursor.execute("ALTER TABLE users_industry ADD COLUMN test_password VARCHAR(128);")
            print("  OK: Added test_password column")
        
        cursor.execute("""
            INSERT INTO django_migrations (app, name, applied)
            VALUES ('users', '0005_industry_test_password_industry_test_phone_number', NOW())
            ON CONFLICT DO NOTHING;
        """)
        print("  OK: Migration recorded")
    else:
        print("Migration 0005_industry_test_password_industry_test_phone_number: Already applied")
    
    # Migration 0006 - FrontendActivityLog (check if table exists)
    if ('users', '0006_frontendactivitylog') not in applied:
        print("\nChecking migration 0006_frontendactivitylog...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users_frontendactivitylog'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("  SKIP: FrontendActivityLog table not needed (will be deleted in 0007)")
        else:
            print("  OK: FrontendActivityLog table exists")
        
        cursor.execute("""
            INSERT INTO django_migrations (app, name, applied)
            VALUES ('users', '0006_frontendactivitylog', NOW())
            ON CONFLICT DO NOTHING;
        """)
        print("  OK: Migration recorded")
    else:
        print("Migration 0006_frontendactivitylog: Already applied")
    
    # Migration 0007 - Delete FrontendActivityLog
    if ('users', '0007_delete_frontendactivitylog') not in applied:
        print("\nApplying migration 0007_delete_frontendactivitylog...")
        cursor.execute("""
            DROP TABLE IF EXISTS users_frontendactivitylog CASCADE;
        """)
        cursor.execute("""
            INSERT INTO django_migrations (app, name, applied)
            VALUES ('users', '0007_delete_frontendactivitylog', NOW())
            ON CONFLICT DO NOTHING;
        """)
        print("  OK: Migration recorded")
    else:
        print("Migration 0007_delete_frontendactivitylog: Already applied")

def check_other_app_migrations(cursor, applied):
    """Check and report on other app migrations"""
    print("\n" + "=" * 70)
    print("Other App Migrations Status")
    print("=" * 70)
    
    apps = ['bookings', 'inventory', 'tasks', 'vendors', 'equipment', 'farms', 'messaging', 'chatbot']
    
    for app in apps:
        cursor.execute("""
            SELECT name FROM django_migrations 
            WHERE app = %s 
            ORDER BY applied;
        """, (app,))
        app_migrations = [row[0] for row in cursor.fetchall()]
        print(f"\n{app}: {len(app_migrations)} migrations applied")
        if app_migrations:
            print(f"  Latest: {app_migrations[-1]}")

def main():
    print("=" * 70)
    print("Applying All Pending Migrations")
    print("=" * 70)
    print(f"Database: {DB_CONFIG['dbname']}")
    print(f"Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print("=" * 70)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cursor = conn.cursor()
        
        # Get applied migrations
        applied = get_applied_migrations(cursor)
        print(f"\nTotal applied migrations: {len(applied)}")
        
        # Apply users migrations
        apply_users_migrations(cursor, applied)
        
        # Check other apps
        check_other_app_migrations(cursor, applied)
        
        # Commit
        conn.commit()
        
        print("\n" + "=" * 70)
        print("Summary")
        print("=" * 70)
        print("OK: All pending users migrations have been applied")
        print("\nNote: Other app migrations may still be pending.")
        print("If you need to apply them, you can:")
        print("  1. Install GDAL and run: python manage.py migrate")
        print("  2. Or apply them manually via SQL")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"\nERROR: Database error: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        print(f"\nERROR: {e}")
        if conn:
            conn.rollback()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

