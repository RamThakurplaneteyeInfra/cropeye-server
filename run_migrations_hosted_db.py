"""
Script to run migrations on hosted database
Usage: python run_migrations_hosted_db.py [--host HOST]
"""
import os
import sys
import argparse
import psycopg2
from psycopg2 import sql

# Default database credentials
DEFAULT_CONFIG = {
    'dbname': 'CROPDB_TEST',
    'user': 'farm_management_l1wj_user',
    'password': 'DySO3fcTFjb8Rgp9IZIxGYgLZ7KxwmjL',
    'port': '5432'
}

def test_connection(host):
    """Test database connection"""
    config = DEFAULT_CONFIG.copy()
    config['host'] = host
    
    try:
        print(f"Testing connection to {host}:{config['port']}...")
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print(f"OK: Connection successful!")
        print(f"PostgreSQL: {version[:60]}...")
        return True
    except psycopg2.Error as e:
        print(f"ERROR: Connection failed: {e}")
        return False

def check_database_state(host):
    """Check current database state"""
    config = DEFAULT_CONFIG.copy()
    config['host'] = host
    
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        # Check users_industry table
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users_industry'
            );
        """)
        industry_exists = cursor.fetchone()[0]
        
        # Check django_migrations table
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'django_migrations'
            );
        """)
        migrations_exists = cursor.fetchone()[0]
        
        applied_migrations = []
        if migrations_exists:
            cursor.execute("""
                SELECT app, name FROM django_migrations 
                ORDER BY app, applied;
            """)
            applied_migrations = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            'industry_exists': industry_exists,
            'migrations_exists': migrations_exists,
            'applied_migrations': applied_migrations
        }
    except Exception as e:
        print(f"ERROR checking database: {e}")
        return None

def create_env_file(host):
    """Create .env file with database credentials"""
    env_content = f"""# Database Configuration - Hosted Database
DB_NAME={DEFAULT_CONFIG['dbname']}
DB_USER={DEFAULT_CONFIG['user']}
DB_PASSWORD={DEFAULT_CONFIG['password']}
DB_HOST={host}
DB_PORT={DEFAULT_CONFIG['port']}

# Django Configuration
DEBUG=True
SECRET_KEY=django-insecure-change-this-in-production
ALLOWED_HOSTS=*
"""
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print(f"OK: Created .env file with host: {host}")
        return True
    except Exception as e:
        print(f"WARNING: Could not create .env file: {e}")
        print("You can set environment variables manually:")
        print(f"  DB_HOST={host}")
        print(f"  DB_NAME={DEFAULT_CONFIG['dbname']}")
        print(f"  DB_USER={DEFAULT_CONFIG['user']}")
        print(f"  DB_PASSWORD={DEFAULT_CONFIG['password']}")
        print(f"  DB_PORT={DEFAULT_CONFIG['port']}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Run migrations on hosted database')
    parser.add_argument('--host', type=str, help='Database host (default: prompt)')
    parser.add_argument('--skip-check', action='store_true', help='Skip database state check')
    args = parser.parse_args()
    
    print("=" * 70)
    print("Django Migration Runner for Hosted Database")
    print("=" * 70)
    
    # Get host
    if args.host:
        host = args.host
    else:
        print("\nPlease provide the database host:")
        print("  - If database is on localhost: localhost")
        print("  - If database is in Docker container: cropeye-db")
        print("  - If database is remote: provide IP or domain name")
        host = input("\nDatabase host: ").strip()
        if not host:
            print("ERROR: Host is required")
            sys.exit(1)
    
    # Test connection
    if not test_connection(host):
        print("\nERROR: Cannot connect to database. Please verify:")
        print("  1. Database is running and accessible")
        print("  2. Host address is correct")
        print("  3. Credentials are correct")
        print("  4. Network/firewall allows connection")
        sys.exit(1)
    
    # Check database state
    if not args.skip_check:
        print("\n" + "=" * 70)
        print("Checking Database State...")
        print("=" * 70)
        state = check_database_state(host)
        if state:
            print(f"\nusers_industry table: {'EXISTS' if state['industry_exists'] else 'MISSING'}")
            print(f"django_migrations table: {'EXISTS' if state['migrations_exists'] else 'MISSING'}")
            if state['applied_migrations']:
                print(f"\nApplied migrations: {len(state['applied_migrations'])}")
                # Group by app
                apps = {}
                for app, name in state['applied_migrations']:
                    if app not in apps:
                        apps[app] = []
                    apps[app].append(name)
                for app in sorted(apps.keys()):
                    print(f"  {app}: {len(apps[app])} migrations")
    
    # Create .env file
    print("\n" + "=" * 70)
    print("Setting up environment...")
    print("=" * 70)
    create_env_file(host)
    
    # Set environment variables for this session
    os.environ['DB_HOST'] = host
    os.environ['DB_NAME'] = DEFAULT_CONFIG['dbname']
    os.environ['DB_USER'] = DEFAULT_CONFIG['user']
    os.environ['DB_PASSWORD'] = DEFAULT_CONFIG['password']
    os.environ['DB_PORT'] = DEFAULT_CONFIG['port']
    
    # Run migrations
    print("\n" + "=" * 70)
    print("Running Django Migrations...")
    print("=" * 70)
    print("\nNote: If you encounter GDAL errors, you may need to:")
    print("  1. Install GDAL library")
    print("  2. Set GDAL_LIBRARY_PATH environment variable")
    print("  3. Or temporarily disable GeoDjango in settings")
    print()
    
    response = input("Proceed with migrations? (y/n): ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        sys.exit(0)
    
    # Import and run Django migrations
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm_management.settings')
        import django
        django.setup()
        from django.core.management import execute_from_command_line
        
        print("\nRunning: python manage.py migrate")
        execute_from_command_line(['manage.py', 'migrate', '--verbosity', '2'])
        print("\n" + "=" * 70)
        print("OK: Migrations completed!")
        print("=" * 70)
    except Exception as e:
        print(f"\nERROR running migrations: {e}")
        print("\nYou can try running migrations manually:")
        print(f"  set DB_HOST={host}")
        print(f"  set DB_NAME={DEFAULT_CONFIG['dbname']}")
        print(f"  set DB_USER={DEFAULT_CONFIG['user']}")
        print(f"  set DB_PASSWORD={DEFAULT_CONFIG['password']}")
        print(f"  set DB_PORT={DEFAULT_CONFIG['port']}")
        print("  python manage.py migrate")
        sys.exit(1)

if __name__ == '__main__':
    main()

