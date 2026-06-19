from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_useractivity'),
    ]

    operations = [
        migrations.AddField(
            model_name='users',
            name='phone',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='users',
            name='department',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='users',
            name='status',
            field=models.CharField(
                blank=True,
                choices=[('active', 'Active'), ('inactive', 'Inactive')],
                default='active',
                max_length=20,
                null=True,
            ),
        ),
    ]