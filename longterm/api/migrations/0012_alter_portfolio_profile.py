# Generated by Django 3.2.4 on 2021-07-06 16:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_auto_20210706_1441'),
    ]

    operations = [
        migrations.AlterField(
            model_name='portfolio',
            name='profile',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='portfolios', to='api.profile'),
        ),
    ]