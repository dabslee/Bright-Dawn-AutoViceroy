# Generated by Django 3.2.9 on 2022-01-09 17:49

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('resource_tracker', '0003_alter_character_approved'),
    ]

    operations = [
        migrations.AddField(
            model_name='trade',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='trade',
            name='buyer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trade_of_buyer', to='resource_tracker.character'),
        ),
        migrations.AlterField(
            model_name='trade',
            name='seller',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trade_of_seller', to='resource_tracker.character'),
        ),
    ]
