# Generated manually - Change CropType plantation_type and planting_method from CharField to ForeignKey

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('farms', '0005_add_plantation_type_and_planting_method'),
    ]

    operations = [
        # Add new ForeignKey fields
        migrations.AddField(
            model_name='croptype',
            name='plantation_type_fk',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='crop_types',
                to='farms.plantationtype',
                help_text='Plantation type for this crop'
            ),
        ),
        migrations.AddField(
            model_name='croptype',
            name='planting_method_fk',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='crop_types',
                to='farms.plantingmethod',
                help_text='Planting method for this crop'
            ),
        ),
        # Add created_at and updated_at fields
        migrations.AddField(
            model_name='croptype',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='croptype',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        # Remove old CharField fields
        migrations.RemoveField(
            model_name='croptype',
            name='plantation_type',
        ),
        migrations.RemoveField(
            model_name='croptype',
            name='planting_method',
        ),
        # Rename new fields to final names
        migrations.RenameField(
            model_name='croptype',
            old_name='plantation_type_fk',
            new_name='plantation_type',
        ),
        migrations.RenameField(
            model_name='croptype',
            old_name='planting_method_fk',
            new_name='planting_method',
        ),
    ]

