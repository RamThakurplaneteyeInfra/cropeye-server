# Generated manually for updating Stock model choices to match frontend requirements

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0009_add_transport_item_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stock',
            name='item_type',
            field=models.CharField(
                choices=[
                    ('logistic', 'Logistic'),
                    ('transport', 'Transport'),
                    ('equipment', 'Equipment'),
                    ('office_purpose', 'Office Purpose'),
                    ('storage', 'Storage'),
                    ('processing', 'Processing'),
                ],
                default='logistic',
                max_length=50,
                verbose_name='Item Type'
            ),
        ),
        migrations.AlterField(
            model_name='stock',
            name='status',
            field=models.CharField(
                choices=[
                    ('working', 'Working'),
                    ('not_working', 'Not working'),
                    ('under_repair', 'underRepair'),
                ],
                default='working',
                max_length=20,
                verbose_name='Status'
            ),
        ),
    ]

