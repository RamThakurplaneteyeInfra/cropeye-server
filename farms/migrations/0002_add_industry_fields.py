# Generated manually for multi-tenant industry support

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('farms', '0001_initial'),
        ('users', '0002_add_industry_multi_tenant'),  # Industry model must exist first
    ]

    operations = [
        migrations.AddField(
            model_name='plot',
            name='industry',
            field=models.ForeignKey(
                blank=True,
                help_text='Industry this plot belongs to',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='plots',
                to='users.industry'
            ),
        ),
        migrations.AddField(
            model_name='farm',
            name='industry',
            field=models.ForeignKey(
                blank=True,
                help_text='Industry this farm belongs to',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='farms',
                to='users.industry'
            ),
        ),
    ]

