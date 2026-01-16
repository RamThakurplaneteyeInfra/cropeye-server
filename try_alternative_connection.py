#!/usr/bin/env python
"""
Try alternative methods to connect to PostgreSQL
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')
DB_HOST = os.environ.get('DB_HOST', 'localhost')

try:
    import psycopg2
except ImportError:
    print("[ERROR] psycopg2 not installed")
    sys.exit(1)

print("Trying different connection methods...\n")

# Method 1: Try localhost with different ports
ports_to_try = [5432, 5433, 5434]

print("Method 1: Trying different ports on localhost")
for port in ports_to_try:
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=port,
            connect_timeout=2
        )
        print(f"[SUCCESS] Connected on port {port}!")
        conn.close()
        sys.exit(0)
    except:
        pass

# Method 2: Try without specifying host (uses default)
print("\nMethod 2: Trying default connection (no host specified)")
try:
    conn = psycopg2.connect(
        dbname='postgres',
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=2
    )
    print("[SUCCESS] Connected using default method!")
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f"[FAILED] {e}")

# Method 3: Try 127.0.0.1 instead of localhost
print("\nMethod 3: Trying 127.0.0.1")
try:
    conn = psycopg2.connect(
        dbname='postgres',
        user=DB_USER,
        password=DB_PASSWORD,
        host='127.0.0.1',
        port=5432,
        connect_timeout=2
    )
    print("[SUCCESS] Connected to 127.0.0.1!")
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f"[FAILED] {e}")

print("\n[ERROR] Could not connect using any method")
print("\nPostgreSQL needs to be configured to accept TCP/IP connections.")
sys.exit(1)

