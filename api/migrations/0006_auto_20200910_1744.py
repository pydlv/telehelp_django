# Generated by Django 3.1.1 on 2020-09-10 22:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_auto_20200910_1741'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active'),
        ),
        migrations.AddField(
            model_name='user',
            name='is_staff',
            field=models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status'),
        ),
    ]
