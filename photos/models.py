from django.contrib.gis.db import models
from django.core.validators import RegexValidator
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from wagtail.snippets.models import register_snippet
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.search import index
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.snippets.edit_handlers import SnippetChooserPanel
import re

''' TODO:
+ .created_at and .modified
'''


@register_snippet
class Photographer(index.Indexed, models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)

    phone_regex = RegexValidator(
        regex=r'^0\d{10}$', message=(
            'Phone number must be entered in the format: "01234567890"; '
            '11 digits allowed.'))
    phone_number = models.CharField(
        validators=[phone_regex], max_length=11, blank=True, null=True)

    AGE_RANGE_CHOICES = [(0, 'undefined')] + [
        (i, '{}-{}'.format(i * 10 - 10, i * 10 - 1))
        for i
        in range(1, 11)
    ]

    age_range = models.PositiveSmallIntegerField(
        choices=AGE_RANGE_CHOICES, default=0
    )

    class Meta:
        ordering = ['last_name', 'first_name', 'email', 'phone_number']
        unique_together = ['email', 'last_name', 'first_name']

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)

    panels = [
        FieldPanel('first_name'),
        FieldPanel('last_name'),
        FieldPanel('email'),
        FieldPanel('phone_number'),
    ]

    search_fields = [
        index.SearchField('first_name', partial_match=True),
        index.SearchField('last_name', partial_match=True),
        index.SearchField('email', partial_match=True),
        index.SearchField('phone_number', partial_match=True),
    ]

    def get_age_range_display(self):
        ret = ''
        for r in self.AGE_RANGE_CHOICES:
            if r[0] == self.age_range:
                ret = r[1]
                break

        return ret

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


@register_snippet
class PhotoCategory(index.Indexed, models.Model):
    label = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50)

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        self.slug = slugify(self.label)
        super().save(*args, **kwargs)

    panels = [
        FieldPanel('label'),
    ]

    search_fields = [
        index.SearchField('label', partial_match=True),
    ]

    class Meta:
        ordering = ['label']
        verbose_name_plural = 'Photo Categories'


@register_snippet
class PhotoSubcategory(index.Indexed, models.Model):
    category = models.ForeignKey(PhotoCategory, on_delete=models.CASCADE)
    label = models.CharField(max_length=60)
    slug = models.SlugField(max_length=60)

    def __str__(self):
        return '{}: {}'.format(self.category.label, self.label)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.label)
        super().save(*args, **kwargs)

    panels = [
        SnippetChooserPanel('category'),
        FieldPanel('label'),
    ]

    search_fields = [
        index.SearchField('label', partial_match=True),
    ]

    class Meta:
        ordering = ['category__label', 'label']
        unique_together = ['label', 'category']
        verbose_name_plural = 'Photo Subcategories'


@register_snippet
class Photo(index.Indexed, models.Model):
    photographer = models.ForeignKey(Photographer, on_delete=models.SET_NULL,
                                     null=True, blank=True, default=None)
    # GN: what does that number represents? What are we doing with it?
    number = models.PositiveSmallIntegerField(default=0, null=True, blank=True)

    # public = models.BooleanField(default=False)
    # image = models.ImageField(upload_to='photos', blank=True, null=True)
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='+'
    )

    description = models.TextField(blank=True, default='')
    comments = models.TextField(blank=True, null=True)

    date = models.DateField(null=True, blank=True)
    location = models.PointField(blank=True, null=True)

    subcategories = models.ManyToManyField(PhotoSubcategory)

    panels = [
        SnippetChooserPanel('photographer'),
        FieldPanel('number'),
        ImageChooserPanel('image'),
        FieldPanel('subcategories'),
        FieldPanel('description'),
        FieldPanel('comments'),
        FieldPanel('date'),
        FieldPanel('location'),
    ]

    search_fields = [
        index.SearchField('description', partial_match=True),
        index.RelatedFields('photographer', [
            index.SearchField('first_name', partial_match=True),
            index.SearchField('last_name', partial_match=True),
        ]),
    ]

    class Meta:
        ordering = ['photographer', 'number']

    def __str__(self):
        return '{} ({}): {}'.format(self.photographer, self.number, self.title)

    @property
    def title(self):
        '''Try to be smart. We stop at the first . or ,'''
        ret = self.description or ''

        if ret:
            ret = re.sub(r'\(.*?\)', '', ret)
            ret = re.sub(r'( -|--).*$', '', ret)
            ret = re.sub(r'[.,;].*$', '', ret)

        max_len = 50
        if len(ret) > max_len:
            ret = ret[:max_len] + '...'

        return ret

    def image_tag(self):
        ret = ''
        if self.image:
            url = self.image.url
            ret = mark_safe(u'<img src="%s" width="50" height="50"/>' % url)
        return ret
    image_tag.short_description = 'Image'
