# Generated by Django 2.0.8 on 2018-12-05 20:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0036_photoflag'),
    ]

    operations = [
        migrations.AlterField(
            model_name='photoflag',
            name='reviewer_comment',
            field=models.TextField(blank=True, null=True),
        ),
    ]
