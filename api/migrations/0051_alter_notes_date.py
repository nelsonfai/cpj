# Generated by Django 3.2.23 on 2024-10-04 14:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0050_rename_canreview_customuser_hasreview'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notes',
            name='date',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]