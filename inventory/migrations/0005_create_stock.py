# Generated manually for adding Stock model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_rename_inventory_in_categor_8b5b0a_idx_inventory_i_categor_fe6a79_idx_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Stock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_name', models.CharField(max_length=200, verbose_name='Item Name')),
                ('item_type', models.CharField(choices=[('logistic', 'Logistic'), ('equipment', 'Equipment'), ('tools', 'Tools'), ('materials', 'Materials'), ('supplies', 'Supplies'), ('other', 'Other')], default='logistic', max_length=50, verbose_name='Item Type')),
                ('make', models.CharField(blank=True, max_length=200, verbose_name='Make')),
                ('year_of_make', models.CharField(blank=True, max_length=10, null=True, verbose_name='Year of Make')),
                ('estimate_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Estimate Cost')),
                ('status', models.CharField(choices=[('working', 'Working'), ('maintenance', 'Under Maintenance'), ('retired', 'Retired'), ('damaged', 'Damaged'), ('available', 'Available')], default='working', max_length=20, verbose_name='Status')),
                ('remark', models.TextField(blank=True, verbose_name='Remark')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_stocks', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Stock',
                'verbose_name_plural': 'Stocks',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='stock',
            index=models.Index(fields=['item_type'], name='inventory_s_item_ty_idx'),
        ),
        migrations.AddIndex(
            model_name='stock',
            index=models.Index(fields=['status'], name='inventory_s_status_idx'),
        ),
        migrations.AddIndex(
            model_name='stock',
            index=models.Index(fields=['item_name'], name='inventory_s_item_na_idx'),
        ),
    ]

