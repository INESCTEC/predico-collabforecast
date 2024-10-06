# Generated by Django 3.2 on 2024-06-19 23:15

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='IndividualForecasts',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField()),
                ('launch_time', models.DateTimeField()),
                ('variable', models.CharField(choices=[('q05', 'Q05'), ('q10', 'Q10'), ('q20', 'Q20'), ('q30', 'Q30'), ('q40', 'Q40'), ('q50', 'Q50'), ('q60', 'Q60'), ('q70', 'Q70'), ('q80', 'Q80'), ('q90', 'Q90'), ('q95', 'Q95'), ('point', 'Point')], max_length=5)),
                ('value', models.FloatField()),
                ('registered_at', models.DateTimeField()),
            ],
            options={
                'db_table': 'individual_forecasts',
            },
        ),
        migrations.CreateModel(
            name='RawData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField()),
                ('value', models.FloatField()),
                ('units', models.CharField(choices=[('w', 'Watt'), ('kw', 'Kilowatt'), ('mw', 'Megawatt')], max_length=2)),
                ('registered_at', models.DateTimeField()),
            ],
            options={
                'db_table': 'raw_data',
            },
        ),
    ]
