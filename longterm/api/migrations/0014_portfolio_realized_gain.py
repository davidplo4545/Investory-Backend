# Generated by Django 3.2.4 on 2021-07-07 09:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_portfoliocomparison_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='portfolio',
            name='realized_gain',
            field=models.FloatField(default=0),
        ),
    ]