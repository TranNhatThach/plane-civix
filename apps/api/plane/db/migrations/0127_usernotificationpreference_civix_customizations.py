# Generated for Civix User Notification & Email Preferences System

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0126_agentconversation_agentpagevector_agentsession_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='usernotificationpreference',
            name='email_assigned',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='usernotificationpreference',
            name='email_due_date',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='usernotificationpreference',
            name='email_digest',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='usernotificationpreference',
            name='email_instant_mention',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='usernotificationpreference',
            name='email_instant_assigned',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='usernotificationpreference',
            name='notify_self_actions',
            field=models.BooleanField(default=False),
        ),
    ]
