# Generated by Django 2.0.8 on 2018-11-26 16:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0033_auto_20181108_0056'),
    ]

    operations = [
        migrations.AlterField(
            model_name='photo',
            name='review_status',
            field=models.IntegerField(choices=[(-1, 'Incomplete submission'), (0, 'Submitted'), (1, 'Public'), (2, 'Archived')], default=0),
        ),
    ]