# Generated by Django 2.0.6 on 2018-06-27 13:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0003_alter_photo'),
    ]

    operations = [
        migrations.AddField(
            model_name='photo',
            name='image',
            field=models.ImageField(default='', upload_to='photos'),
            preserve_default=False,
        ),
    ]
