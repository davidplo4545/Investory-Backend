# Generated by Django 3.2.4 on 2021-07-05 20:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_alter_portfolio_started_at'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='portfolio',
            options={'ordering': ('started_at',)},
        ),
        migrations.AlterModelOptions(
            name='portfolioaction',
            options={'ordering': ('completed_at',)},
        ),
        migrations.AlterModelOptions(
            name='portfoliorecord',
            options={'ordering': ('date',)},
        ),
        migrations.AlterField(
            model_name='portfolio',
            name='name',
            field=models.CharField(max_length=200, unique=True),
        ),
        migrations.CreateModel(
            name='Holding',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.FloatField()),
                ('cost_basis', models.FloatField()),
                ('total_value', models.FloatField(editable=False)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='holdings', to='api.asset')),
                ('portfolio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='holdings', to='api.portfolio')),
            ],
        ),
    ]