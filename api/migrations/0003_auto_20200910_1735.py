# Generated by Django 3.1.1 on 2020-09-10 22:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_auto_20200910_1734'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='provider',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
    ]
