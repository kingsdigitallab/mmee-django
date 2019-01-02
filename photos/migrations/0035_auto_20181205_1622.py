# Generated by Django 2.0.8 on 2018-12-05 16:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0034_auto_20181126_1643'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='photographer',
            options={'ordering': ['-created_at']},
        ),
        migrations.AddField(
            model_name='photographer',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='photographer',
            name='gender',
            field=models.PositiveSmallIntegerField(choices=[(0, 'unspecified'), (1, 'other'), (2, 'female'), (3, 'male')], default=0),
        ),
        migrations.AddField(
            model_name='photographer',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='photographer',
            name='age_range',
            field=models.PositiveSmallIntegerField(choices=[(0, 'unspecified'), (1, '18 and under'), (2, '19-25'), (3, '26-45'), (4, '46-65'), (5, '66 and over')], default=0),
        ),
        migrations.AlterField(
            model_name='photographer',
            name='first_name',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='photographer',
            name='last_name',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='photographer',
            unique_together=set(),
        ),
    ]
