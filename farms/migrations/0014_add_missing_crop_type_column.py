# Generated manually to fix missing ForeignKey columns in Docker database

from django.db import migrations, models
import django.db.models.deletion


def add_missing_foreign_key_columns(apps, schema_editor):
    """Add missing ForeignKey columns if they don't exist"""
    with schema_editor.connection.cursor() as cursor:
        # Check and add crop_type_id column in farms_plantationtype
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'farms_plantationtype' 
            AND column_name = 'crop_type_id'
        """)
        crop_type_column_exists = cursor.fetchone() is not None
        
        if not crop_type_column_exists:
            # Add the crop_type_id column
            cursor.execute("""
                ALTER TABLE farms_plantationtype 
                ADD COLUMN crop_type_id BIGINT NULL
            """)
            
            # Add foreign key constraint
            cursor.execute("""
                ALTER TABLE farms_plantationtype 
                ADD CONSTRAINT farms_plantationtype_crop_type_id_fk 
                FOREIGN KEY (crop_type_id) 
                REFERENCES farms_croptype(id) 
                ON DELETE CASCADE
            """)
            
            # Add index for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS farms_plantationtype_crop_type_id_idx 
                ON farms_plantationtype(crop_type_id)
            """)
        
        # Check and add plantation_type_id column in farms_plantingmethod
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'farms_plantingmethod' 
            AND column_name = 'plantation_type_id'
        """)
        plantation_type_column_exists = cursor.fetchone() is not None
        
        if not plantation_type_column_exists:
            # Add the plantation_type_id column
            cursor.execute("""
                ALTER TABLE farms_plantingmethod 
                ADD COLUMN plantation_type_id BIGINT NULL
            """)
            
            # Add foreign key constraint
            cursor.execute("""
                ALTER TABLE farms_plantingmethod 
                ADD CONSTRAINT farms_plantingmethod_plantation_type_id_fk 
                FOREIGN KEY (plantation_type_id) 
                REFERENCES farms_plantationtype(id) 
                ON DELETE CASCADE
            """)
            
            # Add index for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS farms_plantingmethod_plantation_type_id_idx 
                ON farms_plantingmethod(plantation_type_id)
            """)


def reverse_add_foreign_key_columns(apps, schema_editor):
    """Reverse migration - remove the columns"""
    with schema_editor.connection.cursor() as cursor:
        # Remove crop_type_id from farms_plantationtype
        cursor.execute("""
            ALTER TABLE farms_plantationtype 
            DROP CONSTRAINT IF EXISTS farms_plantationtype_crop_type_id_fk
        """)
        cursor.execute("""
            DROP INDEX IF EXISTS farms_plantationtype_crop_type_id_idx
        """)
        cursor.execute("""
            ALTER TABLE farms_plantationtype 
            DROP COLUMN IF EXISTS crop_type_id
        """)
        
        # Remove plantation_type_id from farms_plantingmethod
        cursor.execute("""
            ALTER TABLE farms_plantingmethod 
            DROP CONSTRAINT IF EXISTS farms_plantingmethod_plantation_type_id_fk
        """)
        cursor.execute("""
            DROP INDEX IF EXISTS farms_plantingmethod_plantation_type_id_idx
        """)
        cursor.execute("""
            ALTER TABLE farms_plantingmethod 
            DROP COLUMN IF EXISTS plantation_type_id
        """)


class Migration(migrations.Migration):

    dependencies = [
        ('farms', '0013_remove_plantationtype_farms_plantationtype_crop_industry_code_unique_and_more'),
    ]

    operations = [
        migrations.RunPython(add_missing_foreign_key_columns, reverse_add_foreign_key_columns),
    ]
