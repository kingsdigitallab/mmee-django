# Generated by Django 2.0.8 on 2018-09-24 02:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0016_auto_20180924_0258'),
    ]

    operations = [
        migrations.AddField(
            model_name='photo',
            name='subcategories',
            field=models.ManyToManyField(to='photos.PhotoSubcategory'),
        ),
    ]