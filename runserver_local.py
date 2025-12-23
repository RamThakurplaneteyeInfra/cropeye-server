#!/usr/bin/env python
"""
Development server script that binds to 0.0.0.0 to allow access from other devices on the same network.
Usage: python runserver_local.py
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm_management.settings')
    django.setup()
    
    # Override sys.argv to run runserver with 0.0.0.0:8000
    sys.argv = ['manage.py', 'runserver', '0.0.0.0:8000']
    
    print("=" * 60)
    print("🚀 Starting Django development server on 0.0.0.0:8000")
    print("=" * 60)
    print("📱 Accessible from other devices on your network:")
    print("   - http://<your-ip-address>:8000")
    print("   - http://localhost:8000 (on this machine)")
    print("=" * 60)
    print()
    
    execute_from_command_line(sys.argv)

