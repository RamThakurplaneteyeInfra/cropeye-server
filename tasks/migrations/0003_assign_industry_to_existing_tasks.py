# Generated manually - Data migration to assign industry to existing tasks

from django.db import migrations


def assign_industry_to_tasks(apps, schema_editor):
    """
    Assign industry to existing tasks based on created_by user's industry.
    """
    Industry = apps.get_model('users', 'Industry')
    Task = apps.get_model('tasks', 'Task')
    
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
    
    # Assign industry to tasks based on created_by's industry
    tasks_updated = 0
    for task in Task.objects.filter(industry__isnull=True):
        if task.created_by and task.created_by.industry:
            task.industry = task.created_by.industry
            task.save()
            tasks_updated += 1
        else:
            # Fallback to default industry
            task.industry = default_industry
            task.save()
            tasks_updated += 1
    
    if tasks_updated > 0:
        print(f"✅ Assigned industry to {tasks_updated} tasks")


def reverse_migration(apps, schema_editor):
    """Reverse migration"""
    Task = apps.get_model('tasks', 'Task')
    Task.objects.all().update(industry=None)
    print("✅ Reversed industry assignments for tasks")


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_add_industry_field'),
        ('users', '0003_create_default_industry'),
    ]

    operations = [
        migrations.RunPython(
            assign_industry_to_tasks,
            reverse_migration
        ),
    ]

