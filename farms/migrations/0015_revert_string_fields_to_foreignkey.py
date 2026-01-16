# Generated manually - Reverse migration to convert CropType plantation_type and planting_method back to ForeignKey
# This migration reverses the changes from the deleted 0015 migration

from django.db import migrations, models
import django.db.models.deletion


def migrate_string_to_foreignkey(apps, schema_editor):
    """
    Migrate data from CharField back to ForeignKey
    Try to match strings to PlantationType and PlantingMethod objects by code or name
    """
    PlantationType = apps.get_model('farms', 'PlantationType')
    PlantingMethod = apps.get_model('farms', 'PlantingMethod')
    
    # Check if we're dealing with string fields (migration 0015 was applied)
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'farms_croptype' 
            AND column_name IN ('plantation_type', 'planting_method')
        """)
        columns = {row[0]: row[1] for row in cursor.fetchall()}
        
        # If columns are character varying (VARCHAR), migration 0015 was applied
        is_string_type = 'plantation_type' in columns and columns['plantation_type'] in ('character varying', 'varchar', 'text')
        
        if is_string_type:
            # Migration 0015 was applied - need to convert back
            
            # Step 1: Add ForeignKey columns
            cursor.execute("""
                ALTER TABLE farms_croptype 
                ADD COLUMN plantation_type_id_temp BIGINT NULL
            """)
            cursor.execute("""
                ALTER TABLE farms_croptype 
                ADD COLUMN planting_method_id_temp BIGINT NULL
            """)
            
            # Step 2: Get all crop types using raw SQL (since ORM won't work with mismatched schema)
            cursor.execute("""
                SELECT id, plantation_type, planting_method 
                FROM farms_croptype
            """)
            crop_types = cursor.fetchall()
            
            # Step 3: Migrate string data to ForeignKey IDs
            for crop_type_id, plantation_type_str, planting_method_str in crop_types:
                plantation_type_id = None
                planting_method_id = None
                
                # Try to find PlantationType by code or name using raw SQL
                if plantation_type_str:
                    # First try by code
                    cursor.execute("""
                        SELECT id FROM farms_plantationtype 
                        WHERE code = %s 
                        LIMIT 1
                    """, [plantation_type_str])
                    result = cursor.fetchone()
                    if result:
                        plantation_type_id = result[0]
                    else:
                        # Try by name
                        cursor.execute("""
                            SELECT id FROM farms_plantationtype 
                            WHERE name = %s 
                            LIMIT 1
                        """, [plantation_type_str])
                        result = cursor.fetchone()
                        if result:
                            plantation_type_id = result[0]
                
                # Try to find PlantingMethod by code or name using raw SQL
                if planting_method_str:
                    # First try by code
                    cursor.execute("""
                        SELECT id FROM farms_plantingmethod 
                        WHERE code = %s 
                        LIMIT 1
                    """, [planting_method_str])
                    result = cursor.fetchone()
                    if result:
                        planting_method_id = result[0]
                    else:
                        # Try by name
                        cursor.execute("""
                            SELECT id FROM farms_plantingmethod 
                            WHERE name = %s 
                            LIMIT 1
                        """, [planting_method_str])
                        result = cursor.fetchone()
                        if result:
                            planting_method_id = result[0]
                
                # Update the temporary ForeignKey columns
                cursor.execute("""
                    UPDATE farms_croptype 
                    SET plantation_type_id_temp = %s, planting_method_id_temp = %s
                    WHERE id = %s
                """, [plantation_type_id, planting_method_id, crop_type_id])
            
            # Step 3: Drop the CharField columns
            cursor.execute("""
                ALTER TABLE farms_croptype 
                DROP COLUMN IF EXISTS plantation_type
            """)
            cursor.execute("""
                ALTER TABLE farms_croptype 
                DROP COLUMN IF EXISTS planting_method
            """)
            
            # Step 4: Rename temporary columns to final names
            cursor.execute("""
                ALTER TABLE farms_croptype 
                RENAME COLUMN plantation_type_id_temp TO plantation_type_id
            """)
            cursor.execute("""
                ALTER TABLE farms_croptype 
                RENAME COLUMN planting_method_id_temp TO planting_method_id
            """)
            
            # Step 5: Add ForeignKey constraints
            cursor.execute("""
                ALTER TABLE farms_croptype 
                ADD CONSTRAINT farms_croptype_plantation_type_id_fk 
                FOREIGN KEY (plantation_type_id) 
                REFERENCES farms_plantationtype(id) 
                ON DELETE SET NULL
            """)
            cursor.execute("""
                ALTER TABLE farms_croptype 
                ADD CONSTRAINT farms_croptype_planting_method_id_fk 
                FOREIGN KEY (planting_method_id) 
                REFERENCES farms_plantingmethod(id) 
                ON DELETE SET NULL
            """)
            
            # Step 6: Add indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS farms_croptype_plantation_type_id_idx 
                ON farms_croptype(plantation_type_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS farms_croptype_planting_method_id_idx 
                ON farms_croptype(planting_method_id)
            """)
        else:
            # Migration 0015 was not applied - database is already in correct state
            # Check if ForeignKey columns already exist
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'farms_croptype' 
                AND column_name IN ('plantation_type_id', 'planting_method_id')
            """)
            fk_columns = [row[0] for row in cursor.fetchall()]
            
            # If ForeignKey columns don't exist, add them (shouldn't happen, but just in case)
            if 'plantation_type_id' not in fk_columns:
                cursor.execute("""
                    ALTER TABLE farms_croptype 
                    ADD COLUMN plantation_type_id BIGINT NULL
                """)
                cursor.execute("""
                    ALTER TABLE farms_croptype 
                    ADD CONSTRAINT farms_croptype_plantation_type_id_fk 
                    FOREIGN KEY (plantation_type_id) 
                    REFERENCES farms_plantationtype(id) 
                    ON DELETE SET NULL
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS farms_croptype_plantation_type_id_idx 
                    ON farms_croptype(plantation_type_id)
                """)
            
            if 'planting_method_id' not in fk_columns:
                cursor.execute("""
                    ALTER TABLE farms_croptype 
                    ADD COLUMN planting_method_id BIGINT NULL
                """)
                cursor.execute("""
                    ALTER TABLE farms_croptype 
                    ADD CONSTRAINT farms_croptype_planting_method_id_fk 
                    FOREIGN KEY (planting_method_id) 
                    REFERENCES farms_plantingmethod(id) 
                    ON DELETE SET NULL
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS farms_croptype_planting_method_id_idx 
                    ON farms_croptype(planting_method_id)
                """)


def reverse_migrate_foreignkey_to_string(apps, schema_editor):
    """
    Reverse migration - convert ForeignKey back to CharField
    This is the reverse of the reverse - so it does what migration 0015 did
    """
    with schema_editor.connection.cursor() as cursor:
        # Check if ForeignKey columns exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'farms_croptype' 
            AND column_name IN ('plantation_type_id', 'planting_method_id')
        """)
        fk_columns = [row[0] for row in cursor.fetchall()]
        
        if 'plantation_type_id' in fk_columns and 'planting_method_id' in fk_columns:
            # Add temporary CharField columns
            cursor.execute("""
                ALTER TABLE farms_croptype 
                ADD COLUMN plantation_type_str VARCHAR(100) NULL
            """)
            cursor.execute("""
                ALTER TABLE farms_croptype 
                ADD COLUMN planting_method_str VARCHAR(100) NULL
            """)
            
            # Get all crop types with ForeignKey IDs using raw SQL
            cursor.execute("""
                SELECT id, plantation_type_id, planting_method_id 
                FROM farms_croptype
            """)
            crop_types = cursor.fetchall()
            
            # Migrate ForeignKey data to strings using raw SQL
            for crop_type_id, plantation_type_id, planting_method_id in crop_types:
                plantation_type_str = None
                planting_method_str = None
                
                if plantation_type_id:
                    # Get code or name from PlantationType
                    cursor.execute("""
                        SELECT code, name FROM farms_plantationtype 
                        WHERE id = %s 
                        LIMIT 1
                    """, [plantation_type_id])
                    result = cursor.fetchone()
                    if result:
                        plantation_type_str = result[0] if result[0] else result[1]
                
                if planting_method_id:
                    # Get code or name from PlantingMethod
                    cursor.execute("""
                        SELECT code, name FROM farms_plantingmethod 
                        WHERE id = %s 
                        LIMIT 1
                    """, [planting_method_id])
                    result = cursor.fetchone()
                    if result:
                        planting_method_str = result[0] if result[0] else result[1]
                
                # Update using parameterized query to avoid SQL injection
                cursor.execute("""
                    UPDATE farms_croptype 
                    SET plantation_type_str = %s, planting_method_str = %s
                    WHERE id = %s
                """, [plantation_type_str, planting_method_str, crop_type_id])
            
            # Drop ForeignKey columns
            cursor.execute("""
                ALTER TABLE farms_croptype 
                DROP CONSTRAINT IF EXISTS farms_croptype_plantation_type_id_fk
            """)
            cursor.execute("""
                ALTER TABLE farms_croptype 
                DROP CONSTRAINT IF EXISTS farms_croptype_planting_method_id_fk
            """)
            cursor.execute("""
                DROP INDEX IF EXISTS farms_croptype_plantation_type_id_idx
            """)
            cursor.execute("""
                DROP INDEX IF EXISTS farms_croptype_planting_method_id_idx
            """)
            cursor.execute("""
                ALTER TABLE farms_croptype 
                DROP COLUMN IF EXISTS plantation_type_id
            """)
            cursor.execute("""
                ALTER TABLE farms_croptype 
                DROP COLUMN IF EXISTS planting_method_id
            """)
            
            # Rename temporary columns
            cursor.execute("""
                ALTER TABLE farms_croptype 
                RENAME COLUMN plantation_type_str TO plantation_type
            """)
            cursor.execute("""
                ALTER TABLE farms_croptype 
                RENAME COLUMN planting_method_str TO planting_method
            """)


class Migration(migrations.Migration):

    dependencies = [
        ('farms', '0014_add_missing_crop_type_column'),
    ]

    operations = [
        migrations.RunPython(migrate_string_to_foreignkey, reverse_migrate_foreignkey_to_string),
    ]

