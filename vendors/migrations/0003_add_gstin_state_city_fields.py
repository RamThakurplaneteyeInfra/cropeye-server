# Generated manually for adding GSTIN, State, and City fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0002_rename_vendors_purch_status_8b5b0a_idx_vendors_pur_status_9a5992_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='gstin_number',
            field=models.CharField(blank=True, help_text='15-digit GSTIN number', max_length=15, null=True, verbose_name='GSTIN Number'),
        ),
        migrations.AddField(
            model_name='vendor',
            name='state',
            field=models.CharField(blank=True, choices=[('Andhra Pradesh', 'Andhra Pradesh'), ('Arunachal Pradesh', 'Arunachal Pradesh'), ('Assam', 'Assam'), ('Bihar', 'Bihar'), ('Chhattisgarh', 'Chhattisgarh'), ('Goa', 'Goa'), ('Gujarat', 'Gujarat'), ('Haryana', 'Haryana'), ('Himachal Pradesh', 'Himachal Pradesh'), ('Jharkhand', 'Jharkhand'), ('Karnataka', 'Karnataka'), ('Kerala', 'Kerala'), ('Madhya Pradesh', 'Madhya Pradesh'), ('Maharashtra', 'Maharashtra'), ('Manipur', 'Manipur'), ('Meghalaya', 'Meghalaya'), ('Mizoram', 'Mizoram'), ('Nagaland', 'Nagaland'), ('Odisha', 'Odisha'), ('Punjab', 'Punjab'), ('Rajasthan', 'Rajasthan'), ('Sikkim', 'Sikkim'), ('Tamil Nadu', 'Tamil Nadu'), ('Telangana', 'Telangana'), ('Tripura', 'Tripura'), ('Uttar Pradesh', 'Uttar Pradesh'), ('Uttarakhand', 'Uttarakhand'), ('West Bengal', 'West Bengal'), ('Andaman and Nicobar Islands', 'Andaman and Nicobar Islands'), ('Chandigarh', 'Chandigarh'), ('Dadra and Nagar Haveli and Daman and Diu', 'Dadra and Nagar Haveli and Daman and Diu'), ('Delhi', 'Delhi'), ('Jammu and Kashmir', 'Jammu and Kashmir'), ('Ladakh', 'Ladakh'), ('Lakshadweep', 'Lakshadweep'), ('Puducherry', 'Puducherry')], max_length=100, null=True, verbose_name='State'),
        ),
        migrations.AddField(
            model_name='vendor',
            name='city',
            field=models.CharField(blank=True, max_length=100, verbose_name='City'),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='contact_person',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='email',
            field=models.EmailField(verbose_name='Email ID'),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='phone',
            field=models.CharField(max_length=20, verbose_name='Mobile Number'),
        ),
        migrations.AddIndex(
            model_name='vendor',
            index=models.Index(fields=['gstin_number'], name='vendors_ven_gstin_n_123abc_idx'),
        ),
    ]

