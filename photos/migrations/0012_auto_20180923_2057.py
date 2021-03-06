# Generated by Django 2.0.8 on 2018-09-23 19:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0011_photo_slug'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='photographer',
            options={'ordering': ['last_name', 'first_name', 'email', 'phone_number']},
        ),
        migrations.AddField(
            model_name='photographer',
            name='first_name',
            field=models.CharField(default='', max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='photographer',
            name='last_name',
            field=models.CharField(default='', max_length=50),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='photographer',
            name='email',
            field=models.EmailField(max_length=254),
        ),
        migrations.RemoveField(
            model_name='photographer',
            name='name',
        ),
        migrations.AlterUniqueTogether(
            name='photographer',
            unique_together={('last_name', 'first_name', 'email')},
        ),
    ]
