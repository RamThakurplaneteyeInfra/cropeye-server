# Generated manually for adding 'transport' item_type to Stock model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0008_add_not_working_status'),
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
                    ('tools', 'Tools'),
                    ('materials', 'Materials'),
                    ('supplies', 'Supplies'),
                    ('other', 'Other'),
                ],
                default='logistic',
                max_length=50,
                verbose_name='Item Type'
            ),
        ),
    ]

