# Generated by Django 3.2.4 on 2021-07-07 12:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_portfolio_realized_gain'),
    ]

    operations = [
        migrations.AlterField(
            model_name='portfolio',
            name='name',
            field=models.CharField(max_length=200),
        ),
    ]
