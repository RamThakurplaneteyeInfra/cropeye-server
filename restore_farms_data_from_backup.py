"""
Restore farms, plots, and farm irrigation data from backup database
"""
import psycopg2
import sys
import os

# Current database (target)
CURRENT_DB = {
    'dbname': 'CROPDB_TEST',
    'user': 'farm_management_l1wj_user',
    'password': 'DySO3fcTFjb8Rgp9IZIxGYgLZ7KxwmjL',
    'host': 'dev-et.cropeye.ai',
    'port': '5432'
}

# Backup database (source) - update these credentials
BACKUP_DB = {
    'dbname': 'farm_management_l1mj',  # Based on filename pattern
    'user': 'farm_management_l1mj_user',  # Update if different
    'password': '',  # Update with backup DB password
    'host': 'dev-et.cropeye.ai',  # Update if different
    'port': '5432'
}

def test_backup_connection():
    """Test connection to backup database"""
    print("=" * 70)
    print("Testing Backup Database Connection")
    print("=" * 70)
    print(f"Host: {BACKUP_DB['host']}")
    print(f"Database: {BACKUP_DB['dbname']}")
    print(f"User: {BACKUP_DB['user']}")
    
    try:
        conn = psycopg2.connect(**BACKUP_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"\nOK: Connected to backup database")
        print(f"PostgreSQL: {version[:60]}...")
        cursor.close()
        conn.close()
        return True
    except psycopg2.Error as e:
        print(f"\nERROR: Could not connect to backup database: {e}")
        print("\nPlease update BACKUP_DB credentials in the script.")
        return False

def get_backup_data(backup_conn, table_name):
    """Get all data from a table in backup database"""
    cursor = backup_conn.cursor()
    
    # Get column names
    cursor.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position;
    """)
    columns = cursor.fetchall()
    column_names = [col[0] for col in columns]
    
    # Get all data
    cursor.execute(f"SELECT * FROM {table_name};")
    rows = cursor.fetchall()
    
    return column_names, rows

def restore_plots(backup_conn, current_conn):
    """Restore plots data"""
    print("\n" + "=" * 70)
    print("Restoring Plots")
    print("=" * 70)
    
    backup_cursor = backup_conn.cursor()
    current_cursor = current_conn.cursor()
    
    # Check if plots exist in backup
    backup_cursor.execute("""
        SELECT COUNT(*) FROM farms_plot;
    """)
    backup_count = backup_cursor.fetchone()[0]
    print(f"Plots in backup: {backup_count}")
    
    if backup_count == 0:
        print("No plots to restore.")
        return 0
    
    # Get all plots from backup
    backup_cursor.execute("""
        SELECT id, gat_number, plot_number, village, taluka, district, state, 
               country, pin_code, location, boundary, created_at, updated_at,
               created_by_id, farmer_id, industry_id
        FROM farms_plot;
    """)
    plots = backup_cursor.fetchall()
    
    # Check existing plots in current DB
    current_cursor.execute("SELECT COUNT(*) FROM farms_plot;")
    current_count = current_cursor.fetchone()[0]
    print(f"Plots in current DB: {current_count}")
    
    restored = 0
    skipped = 0
    
    for plot in plots:
        plot_id, gat_number, plot_number, village, taluka, district, state, \
        country, pin_code, location, boundary, created_at, updated_at, \
        created_by_id, farmer_id, industry_id = plot
        
        # Check if plot already exists (by gat_number, plot_number, village, taluka, district)
        current_cursor.execute("""
            SELECT id FROM farms_plot
            WHERE gat_number = %s AND plot_number = %s 
            AND village = %s AND taluka = %s AND district = %s;
        """, (gat_number, plot_number, village, taluka, district))
        
        if current_cursor.fetchone():
            skipped += 1
            continue
        
        # Insert plot (use new ID, let database generate it)
        current_cursor.execute("""
            INSERT INTO farms_plot (
                gat_number, plot_number, village, taluka, district, state,
                country, pin_code, location, boundary, created_at, updated_at,
                created_by_id, farmer_id, industry_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (gat_number, plot_number, village, taluka, district, state,
              country, pin_code, location, boundary, created_at, updated_at,
              created_by_id, farmer_id, industry_id))
        
        new_plot_id = current_cursor.fetchone()[0]
        restored += 1
        print(f"  Restored plot: {gat_number}/{plot_number} (new ID: {new_plot_id})")
    
    print(f"\nPlots restored: {restored}, skipped (duplicates): {skipped}")
    return restored

def restore_farms(backup_conn, current_conn):
    """Restore farms data"""
    print("\n" + "=" * 70)
    print("Restoring Farms")
    print("=" * 70)
    
    backup_cursor = backup_conn.cursor()
    current_cursor = current_conn.cursor()
    
    # Check if farms exist in backup
    backup_cursor.execute("SELECT COUNT(*) FROM farms_farm;")
    backup_count = backup_cursor.fetchone()[0]
    print(f"Farms in backup: {backup_count}")
    
    if backup_count == 0:
        print("No farms to restore.")
        return 0, {}
    
    # Get all farms from backup with plot_id mapping
    backup_cursor.execute("""
        SELECT f.id, f.farm_uid, f.farm_owner_id, f.created_by_id, f.plot_id,
               f.address, f.area_size, f.farm_document, f.plantation_date,
               f.spacing_a, f.spacing_b, f.created_at, f.updated_at,
               f.crop_type_id, f.soil_type_id, f.industry_id,
               p.gat_number, p.plot_number, p.village, p.taluka, p.district
        FROM farms_farm f
        LEFT JOIN farms_plot p ON f.plot_id = p.id;
    """)
    farms = backup_cursor.fetchall()
    
    # Create mapping: old_plot_id -> new_plot_id
    plot_id_mapping = {}
    current_cursor.execute("""
        SELECT id, gat_number, plot_number, village, taluka, district
        FROM farms_plot;
    """)
    for row in current_cursor.fetchall():
        key = (row[1], row[2], row[3], row[4], row[5])  # gat, plot_num, village, taluka, district
        plot_id_mapping[key] = row[0]
    
    current_cursor.execute("SELECT COUNT(*) FROM farms_farm;")
    current_count = current_cursor.fetchone()[0]
    print(f"Farms in current DB: {current_count}")
    
    restored = 0
    skipped = 0
    farm_id_mapping = {}  # old_farm_id -> new_farm_id
    
    for farm in farms:
        old_farm_id, farm_uid, farm_owner_id, created_by_id, old_plot_id, \
        address, area_size, farm_document, plantation_date, spacing_a, spacing_b, \
        created_at, updated_at, crop_type_id, soil_type_id, industry_id, \
        gat_number, plot_number, village, taluka, district = farm
        
        # Find new plot_id
        new_plot_id = None
        if old_plot_id and gat_number:
            key = (gat_number, plot_number or '', village or '', taluka or '', district or '')
            new_plot_id = plot_id_mapping.get(key)
        
        # Check if farm already exists (by farm_uid)
        current_cursor.execute("SELECT id FROM farms_farm WHERE farm_uid = %s;", (farm_uid,))
        existing = current_cursor.fetchone()
        
        if existing:
            farm_id_mapping[old_farm_id] = existing[0]
            skipped += 1
            continue
        
        # Insert farm
        current_cursor.execute("""
            INSERT INTO farms_farm (
                farm_uid, farm_owner_id, created_by_id, plot_id,
                address, area_size, farm_document, plantation_date,
                spacing_a, spacing_b, created_at, updated_at,
                crop_type_id, soil_type_id, industry_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (farm_uid, farm_owner_id, created_by_id, new_plot_id,
              address, area_size, farm_document, plantation_date,
              spacing_a, spacing_b, created_at, updated_at,
              crop_type_id, soil_type_id, industry_id))
        
        new_farm_id = current_cursor.fetchone()[0]
        farm_id_mapping[old_farm_id] = new_farm_id
        restored += 1
        print(f"  Restored farm: {farm_uid} (new ID: {new_farm_id})")
    
    print(f"\nFarms restored: {restored}, skipped (duplicates): {skipped}")
    return restored, farm_id_mapping

def restore_farm_irrigation(backup_conn, current_conn, farm_id_mapping):
    """Restore farm irrigation data"""
    print("\n" + "=" * 70)
    print("Restoring Farm Irrigation")
    print("=" * 70)
    
    backup_cursor = backup_conn.cursor()
    current_cursor = current_conn.cursor()
    
    # Check if irrigation exists in backup
    backup_cursor.execute("SELECT COUNT(*) FROM farms_farmirrigation;")
    backup_count = backup_cursor.fetchone()[0]
    print(f"Farm irrigation records in backup: {backup_count}")
    
    if backup_count == 0:
        print("No farm irrigation records to restore.")
        return 0
    
    # Get all irrigation from backup
    backup_cursor.execute("""
        SELECT id, location, status, motor_horsepower, pipe_width_inches,
               distance_motor_to_plot_m, plants_per_acre, flow_rate_lph,
               emitters_count, farm_id, irrigation_type_id
        FROM farms_farmirrigation;
    """)
    irrigations = backup_cursor.fetchall()
    
    restored = 0
    skipped = 0
    
    for irrigation in irrigations:
        old_id, location, status, motor_horsepower, pipe_width_inches, \
        distance_motor_to_plot_m, plants_per_acre, flow_rate_lph, \
        emitters_count, old_farm_id, irrigation_type_id = irrigation
        
        # Get new farm_id
        new_farm_id = farm_id_mapping.get(old_farm_id)
        if not new_farm_id:
            skipped += 1
            print(f"  Skipped irrigation (farm_id {old_farm_id} not found)")
            continue
        
        # Insert irrigation
        current_cursor.execute("""
            INSERT INTO farms_farmirrigation (
                location, status, motor_horsepower, pipe_width_inches,
                distance_motor_to_plot_m, plants_per_acre, flow_rate_lph,
                emitters_count, farm_id, irrigation_type_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (location, status, motor_horsepower, pipe_width_inches,
              distance_motor_to_plot_m, plants_per_acre, flow_rate_lph,
              emitters_count, new_farm_id, irrigation_type_id))
        
        new_id = current_cursor.fetchone()[0]
        restored += 1
        print(f"  Restored irrigation (new ID: {new_id})")
    
    print(f"\nFarm irrigation restored: {restored}, skipped: {skipped}")
    return restored

def main():
    print("=" * 70)
    print("Restore Farms Data from Backup Database")
    print("=" * 70)
    
    # Update backup database credentials
    print("\nPlease provide backup database credentials:")
    print("(Press Enter to use defaults or provide new values)")
    
    backup_dbname = input(f"Backup database name [{BACKUP_DB['dbname']}]: ").strip()
    if backup_dbname:
        BACKUP_DB['dbname'] = backup_dbname
    
    backup_user = input(f"Backup database user [{BACKUP_DB['user']}]: ").strip()
    if backup_user:
        BACKUP_DB['user'] = backup_user
    
    backup_password = input("Backup database password: ").strip()
    if backup_password:
        BACKUP_DB['password'] = backup_password
    
    backup_host = input(f"Backup database host [{BACKUP_DB['host']}]: ").strip()
    if backup_host:
        BACKUP_DB['host'] = backup_host
    
    # Test backup connection
    if not test_backup_connection():
        return False
    
    # Connect to both databases
    print("\n" + "=" * 70)
    print("Connecting to databases...")
    print("=" * 70)
    
    try:
        backup_conn = psycopg2.connect(**BACKUP_DB)
        current_conn = psycopg2.connect(**CURRENT_DB)
        backup_conn.autocommit = False
        current_conn.autocommit = False
        
        print("OK: Connected to both databases")
        
        # Restore in order: plots -> farms -> farm_irrigation
        plots_restored = restore_plots(backup_conn, current_conn)
        farms_restored, farm_id_mapping = restore_farms(backup_conn, current_conn)
        irrigation_restored = restore_farm_irrigation(backup_conn, current_conn, farm_id_mapping)
        
        # Commit all changes
        current_conn.commit()
        
        print("\n" + "=" * 70)
        print("Summary")
        print("=" * 70)
        print(f"Plots restored: {plots_restored}")
        print(f"Farms restored: {farms_restored}")
        print(f"Farm irrigation restored: {irrigation_restored}")
        print("\nOK: Data restoration completed!")
        
        backup_conn.close()
        current_conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"\nERROR: Database error: {e}")
        if 'backup_conn' in locals():
            backup_conn.rollback()
            backup_conn.close()
        if 'current_conn' in locals():
            current_conn.rollback()
            current_conn.close()
        return False
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # Allow non-interactive mode
    if '--yes' in sys.argv or '-y' in sys.argv:
        # Use environment variables or defaults
        BACKUP_DB['password'] = os.environ.get('BACKUP_DB_PASSWORD', BACKUP_DB.get('password', ''))
        if not BACKUP_DB['password']:
            print("ERROR: Backup database password required. Set BACKUP_DB_PASSWORD environment variable or run interactively.")
            sys.exit(1)
        test_backup_connection()
    else:
        main()

