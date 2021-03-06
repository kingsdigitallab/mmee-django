# Generated by Django 2.0.8 on 2018-11-08 00:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0032_remove_photo_date'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='photo',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterField(
            model_name='photo',
            name='review_status',
            field=models.IntegerField(choices=[(-1, 'Submission incomplete'), (0, 'Submitted'), (1, 'Public'), (2, 'Archived')], default=0),
        ),
        migrations.AlterField(
            model_name='photo',
            name='subcategories',
            field=models.ManyToManyField(blank=True, null=True, to='photos.PhotoSubcategory'),
        ),
    ]
