# Generated by Django 3.2.23 on 2024-03-15 15:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0029_customuser_productid'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='auto_renew_status',
            field=models.BooleanField(default=False),
        ),
    ]
