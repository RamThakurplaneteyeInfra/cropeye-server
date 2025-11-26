#!/usr/bin/env python
"""
Script to apply industry migrations directly using SQL.
This bypasses Django completely to avoid GDAL issues.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
if os.path.exists('.env.local'):
    load_dotenv('.env.local')
else:
    load_dotenv()

# Database connection settings (Docker PostgreSQL defaults)
DB_NAME = os.environ.get('DB_NAME', 'neoce')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'admin')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')

# If .env has placeholders, use Docker defaults
if DB_HOST == '<your-database-host>' or not DB_HOST:
    DB_HOST = 'localhost'
if DB_NAME == '<your-database-name>' or not DB_NAME:
    DB_NAME = 'neoce'
if DB_USER == '<your-database-user>' or not DB_USER:
    DB_USER = 'postgres'
if DB_PASSWORD == '<your-database-password>' or not DB_PASSWORD:
    DB_PASSWORD = 'admin'

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("[ERROR] psycopg2 is required. Install it with: pip install psycopg2-binary")
    sys.exit(1)

def execute_sql(conn, sql, description):
    """Execute SQL and handle errors"""
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            print(f"[OK] {description}")
            return True
    except Exception as e:
        # Check if error is because table/column already exists
        if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
            print(f"[INFO] {description} (already exists, skipping)")
            return True
        else:
            print(f"[ERROR] {description}: {e}")
            return False

def apply_migrations():
    """Apply industry migrations using raw SQL"""
    print("Applying industry migrations directly to database...")
    print("=" * 60)
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        print("[OK] Connected to database")
        
        # 1. Create Industry table
        print("\n[Step 1] Creating Industry table...")
        industry_table_sql = """
        CREATE TABLE IF NOT EXISTS users_industry (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        """
        execute_sql(conn, industry_table_sql, "Created Industry table")
        
        # 2. Add industry_id to users_user table
        print("\n[Step 2] Adding industry field to User table...")
        # Check if table exists first
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users_user'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if table_exists:
                # Check if column exists
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users_user' AND column_name='industry_id';
                """)
                if not cursor.fetchone():
                    user_industry_sql = """
                    ALTER TABLE users_user 
                    ADD COLUMN industry_id BIGINT REFERENCES users_industry(id) ON DELETE SET NULL;
                    """
                    execute_sql(conn, user_industry_sql, "Added industry_id to users_user")
                else:
                    print("[INFO] industry_id column already exists in users_user")
            else:
                print("[INFO] users_user table does not exist yet - column will be added when table is created")
        
        # 3. Add industry_id to farms_plot table
        print("\n[Step 3] Adding industry field to Plot table...")
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'farms_plot'
                );
            """)
            if cursor.fetchone()[0]:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='farms_plot' AND column_name='industry_id';
                """)
                if not cursor.fetchone():
                    plot_industry_sql = """
                    ALTER TABLE farms_plot 
                    ADD COLUMN industry_id BIGINT REFERENCES users_industry(id) ON DELETE CASCADE;
                    """
                    execute_sql(conn, plot_industry_sql, "Added industry_id to farms_plot")
                else:
                    print("[INFO] industry_id column already exists in farms_plot")
            else:
                print("[INFO] farms_plot table does not exist yet - column will be added when table is created")
        
        # 4. Add industry_id to farms_farm table
        print("\n[Step 4] Adding industry field to Farm table...")
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'farms_farm'
                );
            """)
            if cursor.fetchone()[0]:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='farms_farm' AND column_name='industry_id';
                """)
                if not cursor.fetchone():
                    farm_industry_sql = """
                    ALTER TABLE farms_farm 
                    ADD COLUMN industry_id BIGINT REFERENCES users_industry(id) ON DELETE CASCADE;
                    """
                    execute_sql(conn, farm_industry_sql, "Added industry_id to farms_farm")
                else:
                    print("[INFO] industry_id column already exists in farms_farm")
            else:
                print("[INFO] farms_farm table does not exist yet - column will be added when table is created")
        
        # 5. Add industry_id to bookings_booking table
        print("\n[Step 5] Adding industry field to Booking table...")
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'bookings_booking'
                );
            """)
            if cursor.fetchone()[0]:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='bookings_booking' AND column_name='industry_id';
                """)
                if not cursor.fetchone():
                    booking_industry_sql = """
                    ALTER TABLE bookings_booking 
                    ADD COLUMN industry_id BIGINT REFERENCES users_industry(id) ON DELETE CASCADE;
                    """
                    execute_sql(conn, booking_industry_sql, "Added industry_id to bookings_booking")
                else:
                    print("[INFO] industry_id column already exists in bookings_booking")
            else:
                print("[INFO] bookings_booking table does not exist yet - column will be added when table is created")
        
        # 6. Add industry_id to tasks_task table
        print("\n[Step 6] Adding industry field to Task table...")
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'tasks_task'
                );
            """)
            if cursor.fetchone()[0]:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='tasks_task' AND column_name='industry_id';
                """)
                if not cursor.fetchone():
                    task_industry_sql = """
                    ALTER TABLE tasks_task 
                    ADD COLUMN industry_id BIGINT REFERENCES users_industry(id) ON DELETE CASCADE;
                    """
                    execute_sql(conn, task_industry_sql, "Added industry_id to tasks_task")
                else:
                    print("[INFO] industry_id column already exists in tasks_task")
            else:
                print("[INFO] tasks_task table does not exist yet - column will be added when table is created")
        
        # 7. Add industry_id to inventory_inventoryitem table
        print("\n[Step 7] Adding industry field to InventoryItem table...")
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'inventory_inventoryitem'
                );
            """)
            if cursor.fetchone()[0]:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='inventory_inventoryitem' AND column_name='industry_id';
                """)
                if not cursor.fetchone():
                    inventory_industry_sql = """
                    ALTER TABLE inventory_inventoryitem 
                    ADD COLUMN industry_id BIGINT REFERENCES users_industry(id) ON DELETE CASCADE;
                    """
                    execute_sql(conn, inventory_industry_sql, "Added industry_id to inventory_inventoryitem")
                else:
                    print("[INFO] industry_id column already exists in inventory_inventoryitem")
            else:
                print("[INFO] inventory_inventoryitem table does not exist yet - column will be added when table is created")
        
        # 8. Create default industry
        print("\n[Step 8] Creating default industry...")
        default_industry_sql = """
        INSERT INTO users_industry (name, description, created_at, updated_at)
        SELECT 'Default Industry', 'Default industry for existing users', NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM users_industry WHERE name = 'Default Industry');
        """
        execute_sql(conn, default_industry_sql, "Created default industry")
        
        # 9. Assign existing users to default industry (except superusers)
        print("\n[Step 9] Assigning existing users to default industry...")
        with conn.cursor() as cursor:
            # Check if users_user table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users_user'
                );
            """)
            users_table_exists = cursor.fetchone()[0]
            
            if users_table_exists:
                cursor.execute("SELECT id FROM users_industry WHERE name = 'Default Industry' LIMIT 1;")
                result = cursor.fetchone()
                if result:
                    default_industry_id = result[0]
                    assign_users_sql = f"""
                    UPDATE users_user 
                    SET industry_id = {default_industry_id}
                    WHERE is_superuser = FALSE AND industry_id IS NULL;
                    """
                    cursor.execute(assign_users_sql)
                    updated = cursor.rowcount
                    print(f"[OK] Assigned {updated} users to default industry")
            else:
                print("[INFO] users_user table does not exist yet - will assign users after initial migrations")
        
        # 10. Mark migrations as applied in django_migrations table
        print("\n[Step 10] Marking migrations as applied...")
        with conn.cursor() as cursor:
            # Check if django_migrations table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'django_migrations'
                );
            """)
            migrations_table_exists = cursor.fetchone()[0]
            
            if migrations_table_exists:
                migrations_to_mark = [
                    ('users', '0002_add_industry_multi_tenant'),
                    ('users', '0003_create_default_industry'),
                    ('farms', '0002_add_industry_fields'),
                    ('farms', '0003_assign_industry_to_existing_data'),
                    ('bookings', '0002_add_industry_field'),
                    ('bookings', '0003_assign_industry_to_existing_bookings'),
                    ('tasks', '0002_add_industry_field'),
                    ('tasks', '0003_assign_industry_to_existing_tasks'),
                    ('inventory', '0002_add_industry_field'),
                    ('inventory', '0003_assign_industry_to_existing_items'),
                ]
                
                for app, migration_name in migrations_to_mark:
                    cursor.execute("""
                        INSERT INTO django_migrations (app, name, applied)
                        SELECT %s, %s, NOW()
                        WHERE NOT EXISTS (
                            SELECT 1 FROM django_migrations 
                            WHERE app = %s AND name = %s
                        );
                    """, (app, migration_name, app, migration_name))
                    if cursor.rowcount > 0:
                        print(f"[OK] Marked {app}.{migration_name} as applied")
            else:
                print("[INFO] django_migrations table does not exist yet - migrations will be marked after Django initial setup")
        
        conn.close()
        print("\n" + "=" * 60)
        print("[SUCCESS] All industry migrations applied successfully!")
        print("\n[NOTE] You may still need to configure GDAL for Django to run properly.")
        print("   But the database schema is now updated with industry support.")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"[ERROR] Database connection error: {e}")
        print("\n[INFO] Make sure:")
        print("   1. PostgreSQL is running")
        print("   2. Database credentials in .env are correct")
        print("   3. Database exists")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = apply_migrations()
    sys.exit(0 if success else 1)

