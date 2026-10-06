# Generated for Civix Password Policy & Handover

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0127_usernotificationpreference_civix_customizations'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='must_change_password',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='profile',
            name='temp_password_expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
