# Generated by Django 5.1.1 on 2024-10-11 17:23

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('market', '0003_marketsessionsubmissionscores'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MarketSessionEnsembleWeights',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.FloatField()),
                ('registered_at', models.DateTimeField(auto_now_add=True)),
                ('ensemble', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='market.marketsessionensemble')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'market_session_ensemble_weights',
                'unique_together': {('ensemble', 'user')},
            },
        ),
    ]
