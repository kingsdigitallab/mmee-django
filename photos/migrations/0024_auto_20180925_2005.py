# Generated by Django 2.0.8 on 2018-09-25 19:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0023_auto_20180925_1956'),
    ]

    operations = [
        migrations.AlterField(
            model_name='photo',
            name='number',
            field=models.PositiveSmallIntegerField(blank=True, default=0, null=True),
        ),
    ]
