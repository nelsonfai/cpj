# Generated by Django 3.2.23 on 2024-10-09 22:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0052_habit_sync_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='member1_changed_data',
            field=models.TextField(default='[]'),
        ),
        migrations.AddField(
            model_name='team',
            name='member2_changed_data',
            field=models.TextField(default='[]'),
        ),
    ]