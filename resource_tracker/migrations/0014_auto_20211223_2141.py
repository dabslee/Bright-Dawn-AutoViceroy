# Generated by Django 3.2.9 on 2021-12-24 03:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resource_tracker', '0013_alter_character_created'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='player',
            name='viceroy_gp',
        ),
        migrations.AddField(
            model_name='player',
            name='viceroy_tokens',
            field=models.PositiveIntegerField(default=0),
        ),
    ]