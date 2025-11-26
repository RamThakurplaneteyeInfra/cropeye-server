# Generated manually for adding Order and OrderItem models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0005_alter_purchaseorderitem_options_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice_number', models.CharField(max_length=100, verbose_name='Invoice Number')),
                ('invoice_date', models.DateField(verbose_name='Invoice Date')),
                ('state', models.CharField(choices=[('Andhra Pradesh', 'Andhra Pradesh'), ('Arunachal Pradesh', 'Arunachal Pradesh'), ('Assam', 'Assam'), ('Bihar', 'Bihar'), ('Chhattisgarh', 'Chhattisgarh'), ('Goa', 'Goa'), ('Gujarat', 'Gujarat'), ('Haryana', 'Haryana'), ('Himachal Pradesh', 'Himachal Pradesh'), ('Jharkhand', 'Jharkhand'), ('Karnataka', 'Karnataka'), ('Kerala', 'Kerala'), ('Madhya Pradesh', 'Madhya Pradesh'), ('Maharashtra', 'Maharashtra'), ('Manipur', 'Manipur'), ('Meghalaya', 'Meghalaya'), ('Mizoram', 'Mizoram'), ('Nagaland', 'Nagaland'), ('Odisha', 'Odisha'), ('Punjab', 'Punjab'), ('Rajasthan', 'Rajasthan'), ('Sikkim', 'Sikkim'), ('Tamil Nadu', 'Tamil Nadu'), ('Telangana', 'Telangana'), ('Tripura', 'Tripura'), ('Uttar Pradesh', 'Uttar Pradesh'), ('Uttarakhand', 'Uttarakhand'), ('West Bengal', 'West Bengal'), ('Andaman and Nicobar Islands', 'Andaman and Nicobar Islands'), ('Chandigarh', 'Chandigarh'), ('Dadra and Nagar Haveli and Daman and Diu', 'Dadra and Nagar Haveli and Daman and Diu'), ('Delhi', 'Delhi'), ('Jammu and Kashmir', 'Jammu and Kashmir'), ('Ladakh', 'Ladakh'), ('Lakshadweep', 'Lakshadweep'), ('Puducherry', 'Puducherry')], max_length=100, verbose_name='State')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_orders', to=settings.AUTH_USER_MODEL)),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='vendors.vendor', verbose_name='Vendor Name')),
            ],
            options={
                'verbose_name': 'Order',
                'verbose_name_plural': 'Orders',
                'ordering': ['-invoice_date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_name', models.CharField(max_length=200, verbose_name='Item Name')),
                ('year_of_make', models.CharField(blank=True, max_length=10, null=True, verbose_name='YearOfMake')),
                ('estimate_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='EstimateCost')),
                ('remark', models.TextField(blank=True, verbose_name='Remark')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='vendors.order')),
            ],
            options={
                'verbose_name': 'Order Item',
                'verbose_name_plural': 'Order Items',
                'ordering': ['item_name'],
            },
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['invoice_number'], name='vendors_ord_invoice__idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['invoice_date'], name='vendors_ord_invoice__idx2'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['state'], name='vendors_ord_state_idx'),
        ),
    ]

