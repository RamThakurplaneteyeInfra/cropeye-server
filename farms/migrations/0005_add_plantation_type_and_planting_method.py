# Generated manually for PlantationType and PlantingMethod models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('farms', '0004_plot_farms_plot_gat_num_653494_idx'),  # CropType must exist
        ('users', '0002_add_industry_multi_tenant'),  # Industry model must exist
    ]

    operations = [
        migrations.CreateModel(
            name='PlantationType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Plantation type name (e.g., Adsali, Suru, Kharif)', max_length=100)),
                ('code', models.CharField(blank=True, help_text='Short code for this plantation type (used in CropType.plantation_type field)', max_length=50)),
                ('description', models.TextField(blank=True, help_text='Description of this plantation type')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this plantation type is active')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('crop_type', models.ForeignKey(blank=True, help_text='Crop type this plantation type belongs to', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='plantation_types', to='farms.croptype')),
                ('industry', models.ForeignKey(blank=True, help_text='Industry this plantation type belongs to', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='plantation_types', to='users.industry')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='PlantingMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Planting method name (e.g., 3 Bud Method, Broadcast)', max_length=100)),
                ('code', models.CharField(blank=True, help_text='Short code for this planting method (used in CropType.planting_method field)', max_length=50)),
                ('description', models.TextField(blank=True, help_text='Description of this planting method')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this planting method is active')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('plantation_type', models.ForeignKey(blank=True, help_text='Plantation type this planting method belongs to', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='planting_methods', to='farms.plantationtype')),
                ('industry', models.ForeignKey(blank=True, help_text='Industry this planting method belongs to', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='planting_methods', to='users.industry')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AddConstraint(
            model_name='plantationtype',
            constraint=models.UniqueConstraint(fields=('crop_type', 'industry', 'code'), name='farms_plantationtype_crop_industry_code_unique'),
        ),
        migrations.AddConstraint(
            model_name='plantingmethod',
            constraint=models.UniqueConstraint(fields=('plantation_type', 'industry', 'code'), name='farms_plantingmethod_plantation_industry_code_unique'),
        ),
    ]

