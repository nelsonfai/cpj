# Generated by Django 3.2.23 on 2024-04-01 10:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0030_customuser_auto_renew_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='tourStatusHabitsDone',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='customuser',
            name='tourStatusNotesDone',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='customuser',
            name='tourStatusSharedListDone',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='premium',
            field=models.BooleanField(default=False),
        ),
    ]