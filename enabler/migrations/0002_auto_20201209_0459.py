# Generated by Django 3.1.4 on 2020-12-09 04:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('enabler', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='check',
            old_name='time_range',
            new_name='time_switch',
        ),
    ]