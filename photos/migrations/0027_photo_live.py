# Generated by Django 2.0.8 on 2018-10-21 12:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0026_auto_20180926_0149'),
    ]

    operations = [
        migrations.AddField(
            model_name='photo',
            name='live',
            field=models.BooleanField(default=False),
        ),
    ]