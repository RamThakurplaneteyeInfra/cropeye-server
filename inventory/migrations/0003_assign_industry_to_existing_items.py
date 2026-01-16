# Generated manually - Data migration to assign industry to existing inventory items

from django.db import migrations


def assign_industry_to_inventory_items(apps, schema_editor):
    """
    Assign industry to existing inventory items based on created_by user's industry.
    """
    Industry = apps.get_model('users', 'Industry')
    InventoryItem = apps.get_model('inventory', 'InventoryItem')
    
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
    
    # Assign industry to inventory items based on created_by's industry
    items_updated = 0
    for item in InventoryItem.objects.filter(industry__isnull=True):
        if item.created_by and item.created_by.industry:
            item.industry = item.created_by.industry
            item.save()
            items_updated += 1
        else:
            # Fallback to default industry
            item.industry = default_industry
            item.save()
            items_updated += 1
    
    if items_updated > 0:
        print(f"✅ Assigned industry to {items_updated} inventory items")


def reverse_migration(apps, schema_editor):
    """Reverse migration"""
    InventoryItem = apps.get_model('inventory', 'InventoryItem')
    InventoryItem.objects.all().update(industry=None)
    print("✅ Reversed industry assignments for inventory items")


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_add_industry_field'),
        ('users', '0003_create_default_industry'),
    ]

    operations = [
        migrations.RunPython(
            assign_industry_to_inventory_items,
            reverse_migration
        ),
    ]

