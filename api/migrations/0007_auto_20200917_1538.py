# Generated by Django 3.1.1 on 2020-09-17 20:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_auto_20200910_1744'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='canceled',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='availabilityschedule',
            name='start_date',
            field=models.DateField(),
        ),
    ]
