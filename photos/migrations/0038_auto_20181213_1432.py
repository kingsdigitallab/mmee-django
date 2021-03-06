# Generated by Django 2.0.9 on 2018-12-13 14:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('photos', '0037_auto_20181205_2055'),
    ]

    operations = [
        migrations.AlterField(
            model_name='photo',
            name='review_status',
            field=models.IntegerField(choices=[(0, 'To be reviewed (not public)'), (1, 'Public'), (2, 'Archived (not public)'), (-1, 'Incomplete submission')], default=0),
        ),
        migrations.AlterField(
            model_name='photo',
            name='taken_day',
            field=models.IntegerField(blank=True, default=None, null=True, verbose_name='Day (photo content)'),
        ),
        migrations.AlterField(
            model_name='photo',
            name='taken_month',
            field=models.IntegerField(blank=True, default=None, null=True, verbose_name='Month (photo content)'),
        ),
        migrations.AlterField(
            model_name='photo',
            name='taken_year',
            field=models.IntegerField(blank=True, default=None, null=True, verbose_name='Year (photo content)'),
        ),
        migrations.AlterField(
            model_name='photoflag',
            name='closed',
            field=models.BooleanField(default=False, help_text='Tick to mark the review process complete', verbose_name='resolved'),
        ),
        migrations.AlterField(
            model_name='photoflag',
            name='flagger_comment',
            field=models.TextField(help_text='Please briefly tell us which exact parts of this web page or photo are inappropriate and why you think they are.', max_length=400),
        ),
        migrations.AlterField(
            model_name='photoflag',
            name='photo',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='flags', to='photos.Photo'),
        ),
        migrations.AlterField(
            model_name='photoflag',
            name='reviewer_comment',
            field=models.TextField(blank=True, help_text='Please provide: your name, the date, your opinion after review and the action taken (keep photo live or not, edited content).', null=True),
        ),
    ]
