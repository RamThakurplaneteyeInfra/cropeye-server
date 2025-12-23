"""
Verify the phone number unique index
"""
import psycopg2

DB_CONFIG = {
    'dbname': 'CROPDB_TEST',
    'user': 'farm_management_l1wj_user',
    'password': 'DySO3fcTFjb8Rgp9IZIxGYgLZ7KxwmjL',
    'host': 'dev-et.cropeye.ai',
    'port': '5432'
}

def verify_index():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("=" * 70)
    print("Verifying Phone Number Index")
    print("=" * 70)
    
    # Check indexes
    cursor.execute("""
        SELECT 
            indexname,
            indexdef
        FROM pg_indexes
        WHERE tablename = 'users_user'
        AND indexname LIKE '%phone%'
        ORDER BY indexname;
    """)
    indexes = cursor.fetchall()
    
    print(f"\nFound {len(indexes)} phone number indexes:")
    for name, definition in indexes:
        print(f"\n  {name}:")
        print(f"    {definition}")
    
    # Check if it's unique
    cursor.execute("""
        SELECT 
            i.indexname,
            i.indexdef,
            CASE WHEN idx.indisunique THEN 'UNIQUE' ELSE 'NOT UNIQUE' END as uniqueness
        FROM pg_indexes i
        JOIN pg_index idx ON idx.indexrelid = (
            SELECT oid FROM pg_class WHERE relname = i.indexname
        )
        WHERE i.tablename = 'users_user'
        AND i.indexname LIKE '%phone%';
    """)
    unique_info = cursor.fetchall()
    
    if unique_info:
        print("\nUniqueness information:")
        for name, definition, uniqueness in unique_info:
            print(f"  {name}: {uniqueness}")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    verify_index()

