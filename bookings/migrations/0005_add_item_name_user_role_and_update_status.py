# Generated manually for adding Item Name, User Role fields and updating status choices

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0004_rename_bookings_boo_status_8b5b0a_idx_bookings_bo_status_233e96_idx_and_more'),
        ('users', '0001_initial'),
    ]

    operations = [
        # Add item_name field
        migrations.AddField(
            model_name='booking',
            name='item_name',
            field=models.CharField(blank=True, help_text='Name of the item being booked', max_length=200, verbose_name='Item Name'),
        ),
        # Add user_role field
        migrations.AddField(
            model_name='booking',
            name='user_role',
            field=models.ForeignKey(blank=True, help_text='Role assigned to this booking', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bookings', to='users.role', verbose_name='User Role'),
        ),
        # Make booking_type nullable
        migrations.AlterField(
            model_name='booking',
            name='booking_type',
            field=models.CharField(blank=True, choices=[('meeting', 'Meeting'), ('field', 'Field Work'), ('maintenance', 'Maintenance'), ('training', 'Training'), ('other', 'Other')], max_length=20, null=True),
        ),
        # Update status choices to include 'available' and change default
        migrations.AlterField(
            model_name='booking',
            name='status',
            field=models.CharField(choices=[('available', 'Available'), ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='available', max_length=20),
        ),
    ]

