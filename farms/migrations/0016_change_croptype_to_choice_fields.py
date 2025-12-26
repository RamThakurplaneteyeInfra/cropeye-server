# Generated manually - Change CropType plantation_type and planting_method from ForeignKey to CharField with choices
# This matches the structure from the previous cropeye-server project

from django.db import migrations, models


def migrate_foreignkey_to_choice_string(apps, schema_editor):
    """
    Migrate data from ForeignKey to CharField with choices
    Extract the code or name from PlantationType and PlantingMethod objects
    """
    CropType = apps.get_model('farms', 'CropType')
    PlantationType = apps.get_model('farms', 'PlantationType')
    PlantingMethod = apps.get_model('farms', 'PlantingMethod')
    
    # Mapping of common names to choice values
    plantation_type_mapping = {
        'adsali': 'adsali',
        'suru': 'suru',
        'ratoon': 'ratoon',
        'pre-seasonal': 'pre-seasonal',
        'pre_seasonal': 'pre_seasonal',
        'post-seasonal': 'post-seasonal',
        'post_seasonal': 'post-seasonal',
    }
    
    planting_method_mapping = {
        '3_bud': '3_bud',
        '2_bud': '2_bud',
        '1_bud': '1_bud',
        '1_bud_stip_Method': '1_bud_stip_Method',
        '1_bud_stip_method': '1_bud_stip_Method',
    }
    
    with schema_editor.connection.cursor() as cursor:
        # Check if we're dealing with ForeignKey fields (migration 0015 was not applied or was reverted)
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'farms_croptype' 
            AND column_name IN ('plantation_type_id', 'planting_method_id')
        """)
        fk_columns = {row[0]: row[1] for row in cursor.fetchall()}
        
        is_foreignkey = 'plantation_type_id' in fk_columns and 'planting_method_id' in fk_columns
        
        if is_foreignkey:
            # Migration 0015 was reverted - need to convert from ForeignKey to CharField
            
            # Step 1: Add temporary CharField columns
            cursor.execute("""
                ALTER TABLE farms_croptype 
                ADD COLUMN plantation_type_str VARCHAR(100) NULL
            """)
            cursor.execute("""
                ALTER TABLE farms_croptype 
                ADD COLUMN planting_method_str VARCHAR(100) NULL
            """)
            
            # Step 2: Get all crop types with ForeignKey IDs using raw SQL
            cursor.execute("""
                SELECT id, plantation_type_id, planting_method_id 
                FROM farms_croptype
            """)
            crop_types = cursor.fetchall()
            
            # Step 3: Migrate ForeignKey data to choice strings
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
                        code, name = result
                        # Use code if available, otherwise use name
                        value = code if code else name
                        # Map to choice value
                        plantation_type_str = plantation_type_mapping.get(value.lower(), value.lower())
                        if plantation_type_str not in ['adsali', 'suru', 'ratoon', 'pre-seasonal', 'pre_seasonal', 'post-seasonal', 'other']:
                            plantation_type_str = 'other'
                
                if planting_method_id:
                    # Get code or name from PlantingMethod
                    cursor.execute("""
                        SELECT code, name FROM farms_plantingmethod 
                        WHERE id = %s 
                        LIMIT 1
                    """, [planting_method_id])
                    result = cursor.fetchone()
                    if result:
                        code, name = result
                        # Use code if available, otherwise use name
                        value = code if code else name
                        # Map to choice value
                        planting_method_str = planting_method_mapping.get(value.lower(), value.lower())
                        if planting_method_str not in ['3_bud', '2_bud', '1_bud', '1_bud_stip_Method', 'other']:
                            planting_method_str = 'other'
                
                # Update the temporary CharField columns
                cursor.execute("""
                    UPDATE farms_croptype 
                    SET plantation_type_str = %s, planting_method_str = %s
                    WHERE id = %s
                """, [plantation_type_str, planting_method_str, crop_type_id])
            
            # Step 4: Drop ForeignKey columns and constraints
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
            
            # Step 5: Rename temporary columns to final names
            cursor.execute("""
                ALTER TABLE farms_croptype 
                RENAME COLUMN plantation_type_str TO plantation_type
            """)
            cursor.execute("""
                ALTER TABLE farms_croptype 
                RENAME COLUMN planting_method_str TO planting_method
            """)
        else:
            # Check if CharField already exists (migration 0015 was applied)
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'farms_croptype' 
                AND column_name IN ('plantation_type', 'planting_method')
            """)
            columns = {row[0]: row[1] for row in cursor.fetchall()}
            
            is_string = 'plantation_type' in columns and columns['plantation_type'] in ('character varying', 'varchar', 'text')
            
            if is_string:
                # Already CharField - just ensure data is valid choice values
                cursor.execute("""
                    UPDATE farms_croptype 
                    SET plantation_type = CASE 
                        WHEN plantation_type IN ('adsali', 'suru', 'ratoon', 'pre-seasonal', 'pre_seasonal', 'post-seasonal', 'other') 
                        THEN plantation_type
                        ELSE 'other'
                    END
                    WHERE plantation_type IS NOT NULL AND plantation_type != ''
                """)
                cursor.execute("""
                    UPDATE farms_croptype 
                    SET planting_method = CASE 
                        WHEN planting_method IN ('3_bud', '2_bud', '1_bud', '1_bud_stip_Method', 'other') 
                        THEN planting_method
                        ELSE 'other'
                    END
                    WHERE planting_method IS NOT NULL AND planting_method != ''
                """)


def reverse_migrate_choice_to_foreignkey(apps, schema_editor):
    """
    Reverse migration - convert CharField back to ForeignKey
    This tries to match choice values to PlantationType and PlantingMethod objects
    """
    CropType = apps.get_model('farms', 'CropType')
    PlantationType = apps.get_model('farms', 'PlantationType')
    PlantingMethod = apps.get_model('farms', 'PlantingMethod')
    
    with schema_editor.connection.cursor() as cursor:
        # Check if CharField columns exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'farms_croptype' 
            AND column_name IN ('plantation_type', 'planting_method')
        """)
        char_columns = [row[0] for row in cursor.fetchall()]
        
        if 'plantation_type' in char_columns and 'planting_method' in char_columns:
            # Add temporary ForeignKey columns
            cursor.execute("""
                ALTER TABLE farms_croptype 
                ADD COLUMN plantation_type_id_temp BIGINT NULL
            """)
            cursor.execute("""
                ALTER TABLE farms_croptype 
                ADD COLUMN planting_method_id_temp BIGINT NULL
            """)
            
            # Get all crop types with choice string values using raw SQL
            cursor.execute("""
                SELECT id, plantation_type, planting_method 
                FROM farms_croptype
            """)
            crop_types = cursor.fetchall()
            
            # Migrate choice string data to ForeignKey IDs
            for crop_type_id, plantation_type_str, planting_method_str in crop_types:
                plantation_type_id = None
                planting_method_id = None
                
                if plantation_type_str:
                    # Try to find PlantationType by code or name
                    cursor.execute("""
                        SELECT id FROM farms_plantationtype 
                        WHERE code = %s OR name ILIKE %s 
                        LIMIT 1
                    """, [plantation_type_str, f'%{plantation_type_str}%'])
                    result = cursor.fetchone()
                    if result:
                        plantation_type_id = result[0]
                
                if planting_method_str:
                    # Try to find PlantingMethod by code or name
                    cursor.execute("""
                        SELECT id FROM farms_plantingmethod 
                        WHERE code = %s OR name ILIKE %s 
                        LIMIT 1
                    """, [planting_method_str, f'%{planting_method_str}%'])
                    result = cursor.fetchone()
                    if result:
                        planting_method_id = result[0]
                
                # Update the temporary ForeignKey columns
                cursor.execute("""
                    UPDATE farms_croptype 
                    SET plantation_type_id_temp = %s, planting_method_id_temp = %s
                    WHERE id = %s
                """, [plantation_type_id, planting_method_id, crop_type_id])
            
            # Drop CharField columns
            cursor.execute("""
                ALTER TABLE farms_croptype 
                DROP COLUMN IF EXISTS plantation_type
            """)
            cursor.execute("""
                ALTER TABLE farms_croptype 
                DROP COLUMN IF EXISTS planting_method
            """)
            
            # Rename temporary columns to final names
            cursor.execute("""
                ALTER TABLE farms_croptype 
                RENAME COLUMN plantation_type_id_temp TO plantation_type_id
            """)
            cursor.execute("""
                ALTER TABLE farms_croptype 
                RENAME COLUMN planting_method_id_temp TO planting_method_id
            """)
            
            # Add ForeignKey constraints
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
            
            # Add indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS farms_croptype_plantation_type_id_idx 
                ON farms_croptype(plantation_type_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS farms_croptype_planting_method_id_idx 
                ON farms_croptype(planting_method_id)
            """)


class Migration(migrations.Migration):

    dependencies = [
        ('farms', '0015_revert_string_fields_to_foreignkey'),
    ]

    operations = [
        migrations.RunPython(migrate_foreignkey_to_choice_string, reverse_migrate_choice_to_foreignkey),
        # After data migration, update Django's migration state to reflect CharField
        # We use SeparateDatabaseAndState to update only the state, not the database
        # The database is already updated by RunPython above
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # Database is already updated by RunPython, so no operations needed
            ],
            state_operations=[
                migrations.AlterField(
                    model_name='croptype',
                    name='plantation_type',
                    field=models.CharField(
                        blank=True,
                        choices=[('adsali', 'Adsali'), ('suru', 'Suru'), ('ratoon', 'Ratoon'), ('pre-seasonal', 'Pre-Seasonal'), ('post-seasonal', 'Post-Seasonal'), ('pre_seasonal', 'Pre-Seasonal'), ('other', 'Other')],
                        help_text='Plantation type for this crop',
                        max_length=100
                    ),
                ),
                migrations.AlterField(
                    model_name='croptype',
                    name='planting_method',
                    field=models.CharField(
                        blank=True,
                        choices=[('3_bud', '3 Bud Method'), ('2_bud', '2 Bud Method'), ('1_bud', '1 Bud Method'), ('1_bud_stip_Method', '1 Bud (stip Method)'), ('other', 'Other')],
                        help_text='Planting method for this crop',
                        max_length=100
                    ),
                ),
            ],
        ),
    ]

