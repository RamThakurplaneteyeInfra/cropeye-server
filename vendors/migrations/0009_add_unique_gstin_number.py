# Generated migration to add unique constraint to GSTIN number
# This migration first resolves duplicate GSTINs, then adds the unique constraint

from django.db import migrations, models


def resolve_duplicate_gstins(apps, schema_editor):
    """
    Resolve duplicate GSTIN numbers before adding unique constraint.
    Sets duplicate GSTINs to NULL (keeping only the first occurrence).
    """
    Vendor = apps.get_model('vendors', 'Vendor')
    
    # Find all duplicate GSTINs (excluding NULL)
    from django.db.models import Count
    
    duplicates = Vendor.objects.values('gstin_number').annotate(
        count=Count('gstin_number')
    ).filter(count__gt=1, gstin_number__isnull=False)
    
    # For each duplicate GSTIN, keep the first one and set others to NULL
    for dup in duplicates:
        gstin = dup['gstin_number']
        vendors = Vendor.objects.filter(gstin_number=gstin).order_by('id')
        
        # Keep the first vendor's GSTIN, set others to NULL
        for vendor in vendors[1:]:  # Skip the first one
            vendor.gstin_number = None
            vendor.save(update_fields=['gstin_number'])


def reverse_resolve_duplicate_gstins(apps, schema_editor):
    """
    Reverse operation - nothing to do as we can't restore duplicates
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0008_add_industry_fields'),
    ]

    operations = [
        # Step 1: Resolve duplicate GSTINs
        migrations.RunPython(
            resolve_duplicate_gstins,
            reverse_resolve_duplicate_gstins
        ),
        # Step 2: Add unique constraint
        migrations.AlterField(
            model_name='vendor',
            name='gstin_number',
            field=models.CharField(
                blank=True,
                help_text='15-digit GSTIN number',
                max_length=15,
                null=True,
                unique=True,
                verbose_name='GSTIN Number'
            ),
        ),
    ]
