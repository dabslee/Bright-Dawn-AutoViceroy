# Generated by Django 3.2.9 on 2021-12-23 18:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resource_tracker', '0003_character_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='player',
            name='server_nickname',
        ),
    ]
