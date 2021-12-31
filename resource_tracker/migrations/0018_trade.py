# Generated by Django 3.2.9 on 2021-12-31 00:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('resource_tracker', '0017_auto_20211223_2250'),
    ]

    operations = [
        migrations.CreateModel(
            name='Trade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('seller_verified', models.BooleanField()),
                ('buyer_verified', models.BooleanField()),
                ('money_amount', models.FloatField()),
                ('what_was_purchased', models.TextField(max_length=1000)),
                ('other_stipulations', models.TextField(max_length=1000)),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trade_of_buyer', to='resource_tracker.player')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trade_of_seller', to='resource_tracker.player')),
            ],
        ),
    ]