from django.contrib.gis.db import models
from django.core.validators import RegexValidator


class Photographer(models.Model):
    name = models.CharField(max_length=256)
    email = models.EmailField(unique=True)

    phone_regex = RegexValidator(
        regex=r'^0\d{10}$', message=(
            'Phone number must be entered in the format: "01234567890"; '
            '11 digits allowed.'))
    phone_number = models.CharField(
        validators=[phone_regex], max_length=11, blank=True)

    AGE_RANGE_CHOICES = [(i - 1, '{}-{}'.format(i * 10 - 10, i * 10 - 1))
                         for i in range(1, 11)]

    age_range = models.PositiveSmallIntegerField(
        choices=AGE_RANGE_CHOICES, default=4)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class MonumentType(models.Model):
    title = models.CharField(max_length=128, unique=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class Photo(models.Model):
    photographer = models.ForeignKey(Photographer, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='photos', blank=True, null=True)
    number = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=256)
    date = models.DateField(auto_now_add=True)
    monument_type = models.ManyToManyField(MonumentType, blank=True)
    location = models.PointField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['photographer', 'number']

    def __str__(self):
        return self.title
