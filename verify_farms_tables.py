"""
Verify all farms tables exist
"""
import psycopg2

DB_CONFIG = {
    'dbname': 'CROPDB_TEST',
    'user': 'farm_management_l1wj_user',
    'password': 'DySO3fcTFjb8Rgp9IZIxGYgLZ7KxwmjL',
    'host': 'dev-et.cropeye.ai',
    'port': '5432'
}

def verify_farms_tables():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("=" * 70)
    print("Verifying Farms Tables")
    print("=" * 70)
    
    # Expected tables from farms.0001_initial
    expected_tables = [
        'farms_croptype',
        'farms_irrigationtype',
        'farms_sensortype',
        'farms_soiltype',
        'farms_plot',
        'farms_farm',
        'farms_farmirrigation',
        'farms_farmsensor',
        'farms_farmimage'
    ]
    
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE 'farms_%'
        ORDER BY table_name;
    """)
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    print(f"\nExisting farms tables: {len(existing_tables)}")
    for table in existing_tables:
        print(f"  OK: {table}")
    
    missing = [t for t in expected_tables if t not in existing_tables]
    if missing:
        print(f"\nMissing tables: {len(missing)}")
        for table in missing:
            print(f"  MISSING: {table}")
    else:
        print("\nOK: All expected farms tables exist!")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    verify_farms_tables()

