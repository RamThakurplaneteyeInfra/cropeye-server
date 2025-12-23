# Generated manually for adding industry field to Stock model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0006_rename_inventory_s_item_ty_idx_inventory_s_item_ty_96d067_idx_and_more'),
        ('users', '0002_add_industry_multi_tenant'),  # Industry model is created in this migration
    ]

    operations = [
        migrations.AddField(
            model_name='stock',
            name='industry',
            field=models.ForeignKey(
                blank=True,
                help_text='Industry this stock item belongs to',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='stocks',
                to='users.industry'
            ),
        ),
    ]

