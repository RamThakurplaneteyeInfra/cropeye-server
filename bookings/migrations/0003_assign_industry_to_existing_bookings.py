# Generated manually - Data migration to assign industry to existing bookings

from django.db import migrations


def assign_industry_to_bookings(apps, schema_editor):
    """
    Assign industry to existing bookings based on created_by user's industry.
    """
    Industry = apps.get_model('users', 'Industry')
    Booking = apps.get_model('bookings', 'Booking')
    
    # Get default industry
    try:
        default_industry = Industry.objects.first()
        if not default_industry:
            print("⚠️  No industry found. Creating default industry...")
            default_industry = Industry.objects.create(
                name='Default Industry',
                description='Default industry for existing data'
            )
    except Exception as e:
        print(f"⚠️  Error getting industry: {e}")
        return
    
    # Assign industry to bookings based on created_by's industry
    bookings_updated = 0
    for booking in Booking.objects.filter(industry__isnull=True):
        if booking.created_by and booking.created_by.industry:
            booking.industry = booking.created_by.industry
            booking.save()
            bookings_updated += 1
        else:
            # Fallback to default industry
            booking.industry = default_industry
            booking.save()
            bookings_updated += 1
    
    if bookings_updated > 0:
        print(f"✅ Assigned industry to {bookings_updated} bookings")


def reverse_migration(apps, schema_editor):
    """Reverse migration"""
    Booking = apps.get_model('bookings', 'Booking')
    Booking.objects.all().update(industry=None)
    print("✅ Reversed industry assignments for bookings")


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0002_add_industry_field'),
        ('users', '0003_create_default_industry'),
    ]

    operations = [
        migrations.RunPython(
            assign_industry_to_bookings,
            reverse_migration
        ),
    ]

