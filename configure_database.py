#!/usr/bin/env python
"""
Interactive script to configure PostgreSQL database connection.
This will update your .env file with the correct database settings.
"""

import os
import secrets
from pathlib import Path

def generate_secret_key():
    """Generate a secure Django secret key"""
    return secrets.token_urlsafe(50)

def configure_env_file():
    """Configure .env file with database settings"""
    
    print("=" * 60)
    print("PostgreSQL Database Configuration")
    print("=" * 60)
    print("\nThis script will help you configure your database connection.")
    print("Please provide the following information:\n")
    
    # Get database configuration from user
    print("Enter your PostgreSQL credentials:")
    db_name = input("Database name [neoce]: ").strip() or "neoce"
    db_user = input("Database user [postgres]: ").strip() or "postgres"
    db_password = input("Database password [postgres]: ").strip() or "postgres"
    db_host = input("Database host [localhost]: ").strip() or "localhost"
    db_port = input("Database port [5432]: ").strip() or "5432"
    
    # Generate secret key
    secret_key = generate_secret_key()
    
    # Create .env content
    env_content = f"""# Environment Variables for Local Development
# This file is configured for local PostgreSQL connection

# Django Configuration
DEBUG=True
SECRET_KEY={secret_key}
DJANGO_SETTINGS_MODULE=farm_management.settings
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000

# Database Configuration - Local PostgreSQL
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}
DB_HOST={db_host}
DB_PORT={db_port}

# Redis Configuration (Optional for local development)
# REDIS_URL=redis://localhost:6379/0
# CELERY_BROKER_URL=redis://localhost:6379/0
# CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email Configuration (Optional for local development)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# Frontend URL (Update when you deploy frontend)
FRONTEND_URL=http://localhost:3000
"""
    
    # Write to .env file
    env_path = Path('.env')
    
    if env_path.exists():
        print(f"\n⚠️  Warning: .env file already exists at {env_path.absolute()}")
        response = input("Do you want to overwrite it? (y/N): ").strip().lower()
        if response != 'y':
            print("Cancelled. No changes made.")
            return False
    
    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        print(f"\n✅ Successfully created/updated .env file at {env_path.absolute()}")
        print("\nConfiguration saved:")
        print(f"  Database: {db_name}")
        print(f"  User: {db_user}")
        print(f"  Host: {db_host}:{db_port}")
        return True
    except Exception as e:
        print(f"\n❌ Error writing .env file: {e}")
        print("\nYou may need to create it manually. Here's the content:")
        print("\n" + "=" * 60)
        print(env_content)
        print("=" * 60)
        return False

def test_connection():
    """Test the database connection"""
    print("\n" + "=" * 60)
    print("Testing Database Connection")
    print("=" * 60)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    import psycopg2
    
    DB_NAME = os.environ.get('DB_NAME', 'neoce')
    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    
    try:
        # Try connecting to postgres database first
        conn = psycopg2.connect(
            dbname='postgres',
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        print(f"✅ Successfully connected to PostgreSQL at {DB_HOST}:{DB_PORT}")
        conn.close()
        return True
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL service is running")
        print("2. Check if PostgreSQL is configured to accept connections")
        print("3. Verify your credentials are correct")
        print("4. Check if PostgreSQL is running on a different port")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("PostgreSQL Database Setup for CropEye Server")
    print("=" * 60)
    print()
    
    # Configure .env file
    if configure_env_file():
        print("\n" + "-" * 60)
        test = input("\nDo you want to test the database connection now? (Y/n): ").strip().lower()
        if test != 'n':
            test_connection()
        
        print("\n" + "=" * 60)
        print("Next Steps:")
        print("=" * 60)
        print("1. Run the setup script: python setup_local_database.py")
        print("2. Run migrations: python manage.py migrate")
        print("3. Create superuser: python manage.py createsuperuser")
        print("4. Start server: python manage.py runserver")
        print()

if __name__ == '__main__':
    main()

