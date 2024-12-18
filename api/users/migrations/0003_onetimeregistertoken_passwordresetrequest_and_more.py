# Generated by Django 5.1.1 on 2024-10-25 14:38

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_is_session_manager'),
    ]

    operations = [
        migrations.CreateModel(
            name='OneTimeRegisterToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=500, unique=True)),
                ('used', models.BooleanField(default=False)),
                ('expiration_time', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='PasswordResetRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('token', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.RemoveField(
            model_name='usernotification',
            name='notification_type',
        ),
        migrations.RemoveField(
            model_name='usernotification',
            name='user',
        ),
        migrations.DeleteModel(
            name='UserNotificationType',
        ),
        migrations.DeleteModel(
            name='UserNotification',
        ),
    ]
