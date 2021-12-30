# Generated by Django 3.2.9 on 2021-12-23 18:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Character',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('money', models.FloatField()),
                ('status', models.CharField(choices=[('PA', 'Pre-Approval'), ('AC', 'Active'), ('RD', 'Retired or Dead')], default='NA', max_length=2)),
            ],
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('discord', models.CharField(max_length=50)),
                ('server_nickname', models.CharField(max_length=50)),
                ('downtime', models.PositiveIntegerField()),
                ('spellcaster_hours', models.FloatField()),
                ('role', models.CharField(choices=[('NA', 'None'), ('VR', 'Viceroy'), ('GM', 'Game Master')], default='NA', max_length=2)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Debt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.FloatField()),
                ('creditor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='debt_of_creditor', to='resource_tracker.character')),
                ('debtor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='debt_of_debtor', to='resource_tracker.character')),
            ],
        ),
        migrations.AddField(
            model_name='character',
            name='player',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='resource_tracker.player'),
        ),
    ]
