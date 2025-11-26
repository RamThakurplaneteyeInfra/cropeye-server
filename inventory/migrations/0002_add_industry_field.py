# Generated manually for multi-tenant industry support

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
        ('users', '0002_add_industry_multi_tenant'),  # Industry model must exist first
    ]

    operations = [
        migrations.AddField(
            model_name='inventoryitem',
            name='industry',
            field=models.ForeignKey(
                blank=True,
                help_text='Industry this inventory item belongs to',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='inventory_items',
                to='users.industry'
            ),
        ),
    ]

