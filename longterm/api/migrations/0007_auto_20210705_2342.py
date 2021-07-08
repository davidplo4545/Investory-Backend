# Generated by Django 3.2.4 on 2021-07-05 20:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_auto_20210705_2330'),
    ]

    operations = [
        migrations.AddField(
            model_name='holding',
            name='total_cost',
            field=models.FloatField(default=0, editable=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='holding',
            name='cost_basis',
            field=models.FloatField(editable=False),
        ),
    ]