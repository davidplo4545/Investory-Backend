# Generated by Django 3.2.4 on 2021-07-07 19:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0015_alter_portfolio_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='crypto',
            name='last_updated',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='israelpaper',
            name='last_updated',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='uspaper',
            name='last_updated',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
