# Generated manually - Data migration to assign industry to existing farms and plots

from django.db import migrations


def assign_industry_to_farms_and_plots(apps, schema_editor):
    """
    Assign industry to existing farms and plots based on their farm_owner/created_by user's industry.
    """
    Industry = apps.get_model('users', 'Industry')
    User = apps.get_model('users', 'User')
    Farm = apps.get_model('farms', 'Farm')
    Plot = apps.get_model('farms', 'Plot')
    
    # Get default industry (should exist from previous migration)
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
    
    # Assign industry to farms based on farm_owner's industry
    farms_updated = 0
    for farm in Farm.objects.filter(industry__isnull=True):
        if farm.farm_owner and farm.farm_owner.industry:
            farm.industry = farm.farm_owner.industry
            farm.save()
            farms_updated += 1
        else:
            # Fallback to default industry
            farm.industry = default_industry
            farm.save()
            farms_updated += 1
    
    if farms_updated > 0:
        print(f"✅ Assigned industry to {farms_updated} farms")
    
    # Assign industry to plots based on farmer's industry or created_by's industry
    plots_updated = 0
    for plot in Plot.objects.filter(industry__isnull=True):
        if plot.farmer and plot.farmer.industry:
            plot.industry = plot.farmer.industry
            plot.save()
            plots_updated += 1
        elif plot.created_by and plot.created_by.industry:
            plot.industry = plot.created_by.industry
            plot.save()
            plots_updated += 1
        else:
            # Fallback to default industry
            plot.industry = default_industry
            plot.save()
            plots_updated += 1
    
    if plots_updated > 0:
        print(f"✅ Assigned industry to {plots_updated} plots")


def reverse_migration(apps, schema_editor):
    """
    Reverse migration - set all farms and plots' industry to None
    """
    Farm = apps.get_model('farms', 'Farm')
    Plot = apps.get_model('farms', 'Plot')
    Farm.objects.all().update(industry=None)
    Plot.objects.all().update(industry=None)
    print("✅ Reversed industry assignments for farms and plots")


class Migration(migrations.Migration):

    dependencies = [
        ('farms', '0002_add_industry_fields'),
        ('users', '0003_create_default_industry'),  # Ensure default industry exists
    ]

    operations = [
        migrations.RunPython(
            assign_industry_to_farms_and_plots,
            reverse_migration
        ),
    ]

