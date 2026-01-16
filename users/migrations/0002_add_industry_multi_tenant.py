# Generated manually for multi-tenant industry support

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_industry_table_if_not_exists(apps, schema_editor):
    """Create Industry table only if it doesn't exist"""
    db_alias = schema_editor.connection.alias
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users_industry'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            # Create the table using raw SQL
            cursor.execute("""
                CREATE TABLE users_industry (
                    id BIGSERIAL PRIMARY KEY,
                    name VARCHAR(200) UNIQUE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                );
            """)


def add_industry_column_if_not_exists(apps, schema_editor):
    """Add industry_id column to users_user table if it doesn't exist"""
    db_alias = schema_editor.connection.alias
    with schema_editor.connection.cursor() as cursor:
        # Check if users_user table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users_user'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            # Check if industry_id column exists
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
                # Add the column
                cursor.execute("""
                    ALTER TABLE users_user 
                    ADD COLUMN industry_id BIGINT REFERENCES users_industry(id) ON DELETE SET NULL;
                """)


def reverse_migration(apps, schema_editor):
    """Reverse migration"""
    db_alias = schema_editor.connection.alias
    with schema_editor.connection.cursor() as cursor:
        # Drop column if it exists
        cursor.execute("""
            ALTER TABLE users_user 
            DROP COLUMN IF EXISTS industry_id;
        """)
        # Drop table if it exists
        cursor.execute("DROP TABLE IF EXISTS users_industry CASCADE;")


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            create_industry_table_if_not_exists,
            migrations.RunPython.noop,
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # Database operations are handled by RunPython above
            ],
            state_operations=[
                migrations.CreateModel(
                    name='Industry',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('name', models.CharField(max_length=200, unique=True)),
                        ('description', models.TextField(blank=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                    ],
                    options={
                        'verbose_name': 'Industry',
                        'verbose_name_plural': 'Industries',
                        'ordering': ['name'],
                    },
                ),
            ],
        ),
        migrations.RunPython(
            add_industry_column_if_not_exists,
            migrations.RunPython.noop,
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                # Database operations are handled by RunPython above
            ],
            state_operations=[
                migrations.AddField(
                    model_name='user',
                    name='industry',
                    field=models.ForeignKey(
                        blank=True,
                        help_text='Industry this user belongs to. Null for Global Admin.',
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='users',
                        to='users.industry'
                    ),
                ),
            ],
        ),
    ]

