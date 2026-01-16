# Generated manually for adding Accounting form fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0003_add_gstin_state_city_fields'),
    ]

    operations = [
        # Add invoice fields to PurchaseOrder
        migrations.AddField(
            model_name='purchaseorder',
            name='invoice_date',
            field=models.DateField(blank=True, null=True, verbose_name='Invoice Date'),
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='invoice_number',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Invoice Number'),
        ),
        migrations.AddField(
            model_name='purchaseorder',
            name='state',
            field=models.CharField(blank=True, choices=[('Andhra Pradesh', 'Andhra Pradesh'), ('Arunachal Pradesh', 'Arunachal Pradesh'), ('Assam', 'Assam'), ('Bihar', 'Bihar'), ('Chhattisgarh', 'Chhattisgarh'), ('Goa', 'Goa'), ('Gujarat', 'Gujarat'), ('Haryana', 'Haryana'), ('Himachal Pradesh', 'Himachal Pradesh'), ('Jharkhand', 'Jharkhand'), ('Karnataka', 'Karnataka'), ('Kerala', 'Kerala'), ('Madhya Pradesh', 'Madhya Pradesh'), ('Maharashtra', 'Maharashtra'), ('Manipur', 'Manipur'), ('Meghalaya', 'Meghalaya'), ('Mizoram', 'Mizoram'), ('Nagaland', 'Nagaland'), ('Odisha', 'Odisha'), ('Punjab', 'Punjab'), ('Rajasthan', 'Rajasthan'), ('Sikkim', 'Sikkim'), ('Tamil Nadu', 'Tamil Nadu'), ('Telangana', 'Telangana'), ('Tripura', 'Tripura'), ('Uttar Pradesh', 'Uttar Pradesh'), ('Uttarakhand', 'Uttarakhand'), ('West Bengal', 'West Bengal'), ('Andaman and Nicobar Islands', 'Andaman and Nicobar Islands'), ('Chandigarh', 'Chandigarh'), ('Dadra and Nagar Haveli and Daman and Diu', 'Dadra and Nagar Haveli and Daman and Diu'), ('Delhi', 'Delhi'), ('Jammu and Kashmir', 'Jammu and Kashmir'), ('Ladakh', 'Ladakh'), ('Lakshadweep', 'Lakshadweep'), ('Puducherry', 'Puducherry')], max_length=100, null=True, verbose_name='State'),
        ),
        # Modify PurchaseOrderItem fields
        migrations.AlterField(
            model_name='purchaseorderitem',
            name='inventory_item',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.CASCADE, related_name='purchase_order_items', to='inventory.inventoryitem'),
        ),
        migrations.AddField(
            model_name='purchaseorderitem',
            name='item_name',
            field=models.CharField(blank=True, help_text='Item name if not from inventory', max_length=200, verbose_name='Item Name'),
        ),
        migrations.AddField(
            model_name='purchaseorderitem',
            name='year_of_make',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='YearOfMake'),
        ),
        migrations.AddField(
            model_name='purchaseorderitem',
            name='estimate_cost',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='EstimateCost'),
        ),
        migrations.AddField(
            model_name='purchaseorderitem',
            name='remark',
            field=models.TextField(blank=True, verbose_name='Remark'),
        ),
        # Make quantity and unit_price optional
        migrations.AlterField(
            model_name='purchaseorderitem',
            name='quantity',
            field=models.IntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='purchaseorderitem',
            name='unit_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]

