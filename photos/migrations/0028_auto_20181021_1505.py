# Generated by Django 2.0.8 on 2018-10-21 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0027_photo_live'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='photo',
            name='live',
        ),
        migrations.AddField(
            model_name='photo',
            name='review_status',
            field=models.IntegerField(choices=[(0, 'Submitted'), (1, 'Public'), (2, 'Archived')], default=0),
        ),
    ]
