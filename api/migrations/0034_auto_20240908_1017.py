# Generated by Django 3.2.23 on 2024-09-08 10:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0033_gamification'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='created_at',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='team',
            name='unique_id',
            field=models.CharField(max_length=20, unique=True),
        ),
    ]