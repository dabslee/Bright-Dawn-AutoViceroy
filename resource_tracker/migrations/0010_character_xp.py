# Generated by Django 3.2.9 on 2021-12-23 22:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resource_tracker', '0009_ledgerlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='character',
            name='xp',
            field=models.PositiveIntegerField(default=0),
        ),
    ]