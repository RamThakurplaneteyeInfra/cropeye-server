#!/usr/bin/env python
"""
Complete Database Setup Script
This script will:
1. Check PostgreSQL port and connection settings
2. Create the database (neoce) if it does not exist
3. Install PostGIS extension on the database
4. Test database connection
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("[ERROR] psycopg2 is required. Install it with: pip install psycopg2-binary")
    sys.exit(1)

DB_NAME = os.environ.get('DB_NAME', 'neoce')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)

def print_success(text):
    """Print success message"""
    print(f"[OK] {text}")

def print_error(text):
    """Print error message"""
    print(f"[ERROR] {text}")

def print_info(text):
    """Print info message"""
    print(f"[INFO] {text}")

def print_warning(text):
    """Print warning message"""
    print(f"[WARNING] {text}")

def check_postgresql_settings():
    """Step 1: Check PostgreSQL port and connection settings"""
    print_header("Step 1: Checking PostgreSQL Port and Connection Settings")
    
    print(f"\nConfiguration from .env file:")
    print(f"  Database Name: {DB_NAME}")
    print(f"  Database User: {DB_USER}")
    print(f"  Database Host: {DB_HOST}")
    print(f"  Database Port: {DB_PORT}")
    print(f"  Password: {'*' * len(DB_PASSWORD)} (hidden)")
    
    # Check if we can resolve the host
    import socket
    try:
        socket.gethostbyname(DB_HOST)
        print_success(f"Host '{DB_HOST}' resolves correctly")
    except socket.gaierror:
        print_error(f"Host '{DB_HOST}' cannot be resolved")
        return False
    
    # Check if port is accessible
    print_info(f"Checking if port {DB_PORT} is accessible...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((DB_HOST, int(DB_PORT)))
        sock.close()
        
        if result == 0:
            print_success(f"Port {DB_PORT} is open and accessible")
        else:
            print_error(f"Port {DB_PORT} is not accessible (connection refused)")
            print_warning("PostgreSQL may not be accepting TCP/IP connections")
            return False
    except Exception as e:
        print_error(f"Error checking port: {e}")
        return False
    
    return True

def test_connection_to_postgres():
    """Test connection to default 'postgres' database"""
    print_info("Testing connection to PostgreSQL server (default 'postgres' database)...")
    
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            connect_timeout=5
        )
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print_success("Connected to PostgreSQL server successfully")
            print_info(f"PostgreSQL version: {version.split(',')[0]}")
            
            # Get server settings
            cursor.execute("SHOW port;")
            actual_port = cursor.fetchone()[0]
            cursor.execute("SHOW listen_addresses;")
            listen_addresses = cursor.fetchone()[0]
            
            print_info(f"Server port: {actual_port}")
            print_info(f"Listen addresses: {listen_addresses}")
        
        conn.close()
        return True, None
        
    except psycopg2.OperationalError as e:
        error_msg = str(e)
        print_error(f"Connection failed: {error_msg}")
        
        if "Connection refused" in error_msg or "could not connect" in error_msg:
            print_warning("PostgreSQL is not accepting TCP/IP connections")
            print_info("You may need to:")
            print_info("  1. Configure pg_hba.conf to allow localhost connections")
            print_info("  2. Set listen_addresses = 'localhost' in postgresql.conf")
            print_info("  3. Restart PostgreSQL service")
        elif "password authentication failed" in error_msg:
            print_warning("Password authentication failed")
            print_info("Update DB_PASSWORD in .env file with correct password")
        elif "FATAL" in error_msg:
            print_warning("PostgreSQL connection error")
        
        return False, error_msg
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False, str(e)

def create_database():
    """Step 2: Create the database (neoce) if it does not exist"""
    print_header("Step 2: Creating Database (neoce)")
    
    try:
        # Connect to postgres database
        print_info("Connecting to PostgreSQL server...")
        conn = psycopg2.connect(
            dbname='postgres',
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            connect_timeout=5
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        print_info(f"Checking if database '{DB_NAME}' exists...")
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (DB_NAME,)
        )
        exists = cursor.fetchone()
        
        if exists:
            print_success(f"Database '{DB_NAME}' already exists")
        else:
            print_info(f"Creating database '{DB_NAME}'...")
            cursor.execute(f'CREATE DATABASE "{DB_NAME}"')
            print_success(f"Database '{DB_NAME}' created successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print_error(f"Cannot connect to PostgreSQL: {e}")
        return False
    except psycopg2.DatabaseError as e:
        print_error(f"Database error: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def install_postgis():
    """Step 3: Install PostGIS extension on the database"""
    print_header("Step 3: Installing PostGIS Extension")
    
    try:
        # Connect to the target database
        print_info(f"Connecting to database '{DB_NAME}'...")
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            connect_timeout=5
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if PostGIS is already installed
        print_info("Checking if PostGIS extension is installed...")
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM pg_extension WHERE extname = 'postgis'
            );
        """)
        exists = cursor.fetchone()[0]
        
        if exists:
            print_success("PostGIS extension is already installed")
            
            # Get PostGIS version
            cursor.execute("SELECT PostGIS_version();")
            version = cursor.fetchone()[0]
            print_info(f"PostGIS version: {version}")
        else:
            print_info("Installing PostGIS extension...")
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
                print_success("PostGIS extension installed successfully")
                
                # Get PostGIS version
                cursor.execute("SELECT PostGIS_version();")
                version = cursor.fetchone()[0]
                print_info(f"PostGIS version: {version}")
            except psycopg2.OperationalError as e:
                error_msg = str(e)
                if "extension \"postgis\" does not exist" in error_msg.lower():
                    print_error("PostGIS extension is not available on this PostgreSQL server")
                    print_warning("PostGIS needs to be installed on PostgreSQL server")
                    print_info("For Windows:")
                    print_info("  1. Download PostGIS installer from: https://postgis.net/install/")
                    print_info("  2. Install PostGIS for PostgreSQL 17")
                    print_info("  3. Run this script again")
                    return False
                else:
                    raise
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print_error(f"Cannot connect to database: {e}")
        return False
    except Exception as e:
        print_error(f"Error installing PostGIS: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """Step 4: Test database connection"""
    print_header("Step 4: Testing Database Connection")
    
    try:
        print_info(f"Connecting to database '{DB_NAME}'...")
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            connect_timeout=5
        )
        
        # Test basic query
        cursor = conn.cursor()
        cursor.execute("SELECT current_database(), current_user, version();")
        db_name, user, version = cursor.fetchone()
        
        print_success(f"Successfully connected to database '{db_name}'")
        print_info(f"Connected as user: {user}")
        print_info(f"PostgreSQL version: {version.split(',')[0]}")
        
        # Check PostGIS
        cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'postgis');")
        has_postgis = cursor.fetchone()[0]
        
        if has_postgis:
            cursor.execute("SELECT PostGIS_version();")
            postgis_version = cursor.fetchone()[0]
            print_success(f"PostGIS is installed: {postgis_version}")
        else:
            print_warning("PostGIS is not installed")
        
        # Test GeoDjango compatibility
        try:
            cursor.execute("SELECT PostGIS_full_version();")
            postgis_full = cursor.fetchone()[0]
            print_info("GeoDjango compatibility: OK")
        except:
            print_warning("GeoDjango compatibility check failed")
        
        # List tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        if tables:
            print_info(f"Database contains {len(tables)} tables")
            if len(tables) <= 10:
                print_info("Tables: " + ", ".join([t[0] for t in tables]))
        else:
            print_info("Database is empty (no tables yet)")
            print_info("Run migrations to create tables: python manage.py migrate")
        
        cursor.close()
        conn.close()
        
        print_success("Database connection test completed successfully!")
        return True
        
    except psycopg2.OperationalError as e:
        print_error(f"Connection failed: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main execution function"""
    print("\n" + "=" * 60)
    print("Complete Database Setup")
    print("=" * 60)
    print(f"\nTarget Database: {DB_NAME}")
    print(f"PostgreSQL Server: {DB_HOST}:{DB_PORT}")
    print(f"User: {DB_USER}")
    
    results = {
        'settings_check': False,
        'connection_test': False,
        'database_created': False,
        'postgis_installed': False,
        'final_test': False
    }
    
    # Step 1: Check PostgreSQL settings
    results['settings_check'] = check_postgresql_settings()
    
    if not results['settings_check']:
        print("\n[FAILED] Cannot proceed - PostgreSQL settings check failed")
        print("\nPlease fix PostgreSQL configuration first:")
        print("  1. Make sure PostgreSQL service is running")
        print("  2. Configure pg_hba.conf to allow localhost connections")
        print("  3. Set listen_addresses = 'localhost' in postgresql.conf")
        print("  4. Restart PostgreSQL service")
        return False
    
    # Test connection to postgres database
    connected, error = test_connection_to_postgres()
    results['connection_test'] = connected
    
    if not connected:
        print("\n[FAILED] Cannot connect to PostgreSQL server")
        if error:
            print(f"Error: {error}")
        return False
    
    # Step 2: Create database
    results['database_created'] = create_database()
    
    if not results['database_created']:
        print("\n[FAILED] Cannot create database")
        return False
    
    # Step 3: Install PostGIS
    results['postgis_installed'] = install_postgis()
    
    if not results['postgis_installed']:
        print("\n[WARNING] PostGIS installation failed or not available")
        print("You can continue without PostGIS, but GeoDjango features won't work")
        print("For now, continuing with tests...")
    
    # Step 4: Test final connection
    results['final_test'] = test_database_connection()
    
    # Summary
    print_header("Setup Summary")
    
    print("\nResults:")
    print(f"  Settings Check:        {'[OK]' if results['settings_check'] else '[FAILED]'}")
    print(f"  Server Connection:     {'[OK]' if results['connection_test'] else '[FAILED]'}")
    print(f"  Database Created:      {'[OK]' if results['database_created'] else '[FAILED]'}")
    print(f"  PostGIS Installed:     {'[OK]' if results['postgis_installed'] else '[FAILED/WARNING]'}")
    print(f"  Final Connection Test: {'[OK]' if results['final_test'] else '[FAILED]'}")
    
    if results['final_test']:
        print("\n" + "=" * 60)
        print("SUCCESS! Database is ready!")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Run migrations: python manage.py migrate")
        print("  2. Create superuser: python manage.py createsuperuser")
        print("  3. Start server: python manage.py runserver")
        return True
    else:
        print("\n[FAILED] Database setup incomplete")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

