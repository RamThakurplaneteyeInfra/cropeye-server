# Generated manually - Data migration to create default industry and assign existing users

from django.db import migrations


def create_default_industry_and_assign_users(apps, schema_editor):
    """
    Create a default industry and assign all existing users to it.
    Global Admin (is_superuser=True) will remain with industry=None.
    """
    db_alias = schema_editor.connection.alias
    
    # Check if industry_id column exists
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'users_user' 
                AND column_name = 'industry_id'
            );
        """)
        column_exists = cursor.fetchone()[0]
        
        if not column_exists:
            print("⚠️  industry_id column does not exist yet - skipping user assignment")
            return
    
    Industry = apps.get_model('users', 'Industry')
    User = apps.get_model('users', 'User')
    
    # Create default industry if it doesn't exist
    default_industry, created = Industry.objects.get_or_create(
        name='Default Industry',
        defaults={
            'description': 'Default industry for existing users'
        }
    )
    
    if created:
        print(f"✅ Created default industry: {default_industry.name}")
    else:
        print(f"ℹ️  Default industry already exists: {default_industry.name}")
    
    # Check if users_user table exists and has any users
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users_user'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("ℹ️  users_user table does not exist yet - skipping user assignment")
            return
    
    # Assign all non-superuser users to the default industry
    users_updated = User.objects.filter(
        is_superuser=False,
        industry__isnull=True
    ).update(industry=default_industry)
    
    if users_updated > 0:
        print(f"✅ Assigned {users_updated} users to default industry")
    else:
        print("ℹ️  No users needed assignment")


def reverse_migration(apps, schema_editor):
    """
    Reverse migration - set all users' industry to None
    """
    User = apps.get_model('users', 'User')
    User.objects.all().update(industry=None)
    print("✅ Reversed industry assignments")


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_add_industry_multi_tenant'),
    ]

    operations = [
        migrations.RunPython(
            create_default_industry_and_assign_users,
            reverse_migration
        ),
    ]

