# Generated manually for adding 'not_working' status to Stock model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0007_add_industry_field_to_stock'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stock',
            name='status',
            field=models.CharField(
                choices=[
                    ('working', 'Working'),
                    ('maintenance', 'Under Maintenance'),
                    ('retired', 'Retired'),
                    ('damaged', 'Damaged'),
                    ('available', 'Available'),
                    ('not_working', 'Not working'),
                ],
                default='working',
                max_length=20,
                verbose_name='Status'
            ),
        ),
    ]

