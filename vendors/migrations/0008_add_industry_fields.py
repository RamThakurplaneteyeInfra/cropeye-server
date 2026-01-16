# Generated manually for adding industry fields to Vendor and Order models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0007_rename_vendors_ord_invoice__idx_vendors_ord_invoice_4bc631_idx_and_more'),
        ('users', '0002_add_industry_multi_tenant'),  # Industry model is created in this migration
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='industry',
            field=models.ForeignKey(
                blank=True,
                help_text='Industry this vendor belongs to',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='vendors',
                to='users.industry'
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='industry',
            field=models.ForeignKey(
                blank=True,
                help_text='Industry this order belongs to',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='orders',
                to='users.industry'
            ),
        ),
    ]

