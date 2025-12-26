# Generated manually - Add industry field to CropType model

from django.db import migrations, models
import django.db.models.deletion


def assign_default_industry_to_croptypes(apps, schema_editor):
    """
    Assign default industry to existing CropType records
    """
    Industry = apps.get_model('users', 'Industry')
    CropType = apps.get_model('farms', 'CropType')
    
    # Get default industry (first industry or create one)
    try:
        default_industry = Industry.objects.first()
        if not default_industry:
            print("⚠️  No industry found. Creating default industry...")
            default_industry = Industry.objects.create(
                name='Default Industry',
                description='Default industry for existing crop types'
            )
            print(f"✅ Created default industry: {default_industry.name}")
        else:
            print(f"ℹ️  Using existing industry: {default_industry.name}")
    except Exception as e:
        print(f"⚠️  Error getting industry: {e}")
        return
    
    # Assign default industry to all existing CropType records
    crop_types_updated = CropType.objects.filter(industry__isnull=True).update(industry=default_industry)
    if crop_types_updated > 0:
        print(f"✅ Assigned industry to {crop_types_updated} crop types")


def reverse_assign_industry(apps, schema_editor):
    """Reverse migration - remove industry assignment"""
    CropType = apps.get_model('farms', 'CropType')
    CropType.objects.all().update(industry=None)


class Migration(migrations.Migration):

    dependencies = [
        ('farms', '0016_change_croptype_to_choice_fields'),
        ('users', '0001_initial'),  # Ensure Industry model exists
    ]

    operations = [
        migrations.AddField(
            model_name='croptype',
            name='industry',
            field=models.ForeignKey(
                blank=True,
                help_text='Industry this crop type belongs to',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='crop_types',
                to='users.industry'
            ),
        ),
        migrations.RunPython(assign_default_industry_to_croptypes, reverse_assign_industry),
    ]

