"""
Direct SQL script to create industries table and apply related migrations
This can be used if Django migrations fail due to GDAL or other issues
"""
import psycopg2
from psycopg2 import sql
import sys

# Database credentials
DB_CONFIG = {
    'dbname': 'CROPDB_TEST',
    'user': 'farm_management_l1wj_user',
    'password': 'DySO3fcTFjb8Rgp9IZIxGYgLZ7KxwmjL',
    'host': 'localhost',  # Change this to your actual database host
    'port': '5432'
}

def apply_industry_migration():
    """Apply industry table migration directly via SQL"""
    
    print("=" * 70)
    print("Applying Industry Migration Directly via SQL")
    print("=" * 70)
    print(f"Database: {DB_CONFIG['dbname']}")
    print(f"Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"User: {DB_CONFIG['user']}")
    print("=" * 70)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cursor = conn.cursor()
        
        print("\n1. Checking if users_industry table exists...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users_industry'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("   OK: users_industry table already exists")
            
            # Check table structure
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns
                WHERE table_name = 'users_industry'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            print(f"   Columns: {', '.join([c[0] for c in columns])}")
            
            # Check if test_phone_number and test_password columns exist
            column_names = [c[0] for c in columns]
            needs_update = False
            
            if 'test_phone_number' not in column_names:
                print("   MISSING: test_phone_number column")
                needs_update = True
            if 'test_password' not in column_names:
                print("   MISSING: test_password column")
                needs_update = True
            
            if needs_update:
                print("\n2. Adding missing columns to users_industry table...")
                if 'test_phone_number' not in column_names:
                    cursor.execute("""
                        ALTER TABLE users_industry 
                        ADD COLUMN test_phone_number VARCHAR(15);
                    """)
                    print("   OK: Added test_phone_number column")
                
                if 'test_password' not in column_names:
                    cursor.execute("""
                        ALTER TABLE users_industry 
                        ADD COLUMN test_password VARCHAR(128);
                    """)
                    print("   OK: Added test_password column")
                
                conn.commit()
                print("   OK: Table updated successfully")
            else:
                print("   OK: Table structure is complete")
        else:
            print("   MISSING: users_industry table does not exist")
            print("\n2. Creating users_industry table...")
            
            cursor.execute("""
                CREATE TABLE users_industry (
                    id BIGSERIAL PRIMARY KEY,
                    name VARCHAR(200) UNIQUE NOT NULL,
                    description TEXT,
                    test_phone_number VARCHAR(15),
                    test_password VARCHAR(128),
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                );
            """)
            
            # Create index on name for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS users_industry_name_idx 
                ON users_industry(name);
            """)
            
            conn.commit()
            print("   OK: users_industry table created successfully")
        
        # Check if industry_id column exists in users_user table
        print("\n3. Checking users_user table for industry_id column...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'users_user' 
                AND column_name = 'industry_id'
            );
        """)
        column_exists = cursor.fetchone()[0]
        
        if not column_exists:
            print("   MISSING: industry_id column in users_user table")
            print("   Adding industry_id column...")
            
            cursor.execute("""
                ALTER TABLE users_user 
                ADD COLUMN industry_id BIGINT;
            """)
            
            # Add foreign key constraint
            cursor.execute("""
                ALTER TABLE users_user 
                ADD CONSTRAINT users_user_industry_id_fkey 
                FOREIGN KEY (industry_id) 
                REFERENCES users_industry(id) 
                ON DELETE SET NULL;
            """)
            
            # Create index
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS users_user_industry_id_idx 
                ON users_user(industry_id);
            """)
            
            conn.commit()
            print("   OK: industry_id column added to users_user table")
        else:
            print("   OK: industry_id column already exists")
        
        # Check django_migrations table
        print("\n4. Updating django_migrations table...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'django_migrations'
            );
        """)
        migrations_table_exists = cursor.fetchone()[0]
        
        if migrations_table_exists:
            # Check if migration is already recorded
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM django_migrations 
                    WHERE app = 'users' 
                    AND name = '0002_add_industry_multi_tenant'
                );
            """)
            migration_recorded = cursor.fetchone()[0]
            
            if not migration_recorded:
                print("   Recording migration in django_migrations...")
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied)
                    VALUES ('users', '0002_add_industry_multi_tenant', NOW())
                    ON CONFLICT DO NOTHING;
                """)
                conn.commit()
                print("   OK: Migration recorded")
            else:
                print("   OK: Migration already recorded")
        else:
            print("   WARNING: django_migrations table does not exist")
            print("   This is normal if migrations have never been run")
        
        # Summary
        print("\n" + "=" * 70)
        print("Summary:")
        print("=" * 70)
        cursor.execute("SELECT COUNT(*) FROM users_industry;")
        industry_count = cursor.fetchone()[0]
        print(f"OK: users_industry table exists with {industry_count} records")
        print("OK: industry_id column exists in users_user table")
        print("\nNext steps:")
        print("  1. Run other pending migrations: python manage.py migrate")
        print("  2. Create default industry if needed")
        print("  3. Assign existing users to industries if needed")
        
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
    # Allow host to be passed as command line argument
    if len(sys.argv) > 1:
        DB_CONFIG['host'] = sys.argv[1]
        print(f"Using host: {DB_CONFIG['host']}")
    
    success = apply_industry_migration()
    sys.exit(0 if success else 1)

