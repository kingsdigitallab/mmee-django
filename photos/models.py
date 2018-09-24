from django.contrib.gis.db import models
from django.core.validators import RegexValidator


class Photographer(models.Model):
    # name = models.CharField(max_length=256)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)

    phone_regex = RegexValidator(
        regex=r'^0\d{10}$', message=(
            'Phone number must be entered in the format: "01234567890"; '
            '11 digits allowed.'))
    phone_number = models.CharField(
        validators=[phone_regex], max_length=11, blank=True, null=True)

    AGE_RANGE_CHOICES = [(0, 'undefined')] +\
        [
            (i, '{}-{}'.format(i * 10 - 10, i * 10 - 1))
            for i
            in range(1, 11)
    ]

    age_range = models.PositiveSmallIntegerField(
        choices=AGE_RANGE_CHOICES, default=0
    )

    class Meta:
        ordering = ['last_name', 'first_name', 'email', 'phone_number']
        unique_together = ['last_name', 'first_name', 'email']

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)

    @classmethod
    def get_age_range_from_str(cls, age_range):
        '''10-19 => 2'''
        ret = 0
        if age_range:
            for k, rng in cls.AGE_RANGE_CHOICES:
                if age_range == rng:
                    ret = k
            if ret == 0:
                raise('Invalid date range {}'.format(age_range))
        return ret


class MonumentType(models.Model):
    title = models.CharField(max_length=128, unique=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class Photo(models.Model):
    photographer = models.ForeignKey(Photographer, on_delete=models.CASCADE)
    public = models.BooleanField(default=False)
    image = models.ImageField(upload_to='photos', blank=True, null=True)
    # GN: what does that number represents? What are we doing with it?
    number = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=256)
    date = models.DateField()
    monument_type = models.ManyToManyField(MonumentType, blank=True)
    location = models.PointField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['photographer', 'number']

    def __str__(self):
        return self.title
