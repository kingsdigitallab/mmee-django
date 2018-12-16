from django.contrib.gis.db import models
from django.core.validators import RegexValidator
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from wagtail.snippets.models import register_snippet
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.search import index
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.snippets.edit_handlers import SnippetChooserPanel
from wagtail.images.shortcuts import get_rendition_or_not_found
from collections import OrderedDict
from django.utils import timezone
import datetime
import re

''' TODO:
'''

DEFAULT_CREATED_AT = timezone.make_aware(datetime.datetime(1980, 1, 1))


@register_snippet
class PhotoFlag(models.Model):
    '''
    Represents a comment from a web user
    about the inappropriateness of a Photo record.
    '''
    photo = models.ForeignKey(
        'Photo', on_delete=models.CASCADE,
        related_name='flags'
    )
    flagger_comment = models.TextField(
        max_length=400,
        help_text='Please briefly tell us which exact parts of this web page'
        ' or photo are inappropriate and why you think they are.'
    )
    reviewer_comment = models.TextField(
        blank=True, null=True,
        help_text='Please provide: your name, the date, your opinion after'
        ' review and the action taken'
        ' (keep photo live or not, edited content).'
    )
    closed = models.BooleanField(
        'resolved', default=False,
        help_text='Tick to mark the review process complete'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'Photo Flag #{}'.format(self.pk)

    panels = [
        FieldPanel('flagger_comment'),
        FieldPanel('reviewer_comment'),
        FieldPanel('closed'),
        SnippetChooserPanel('photo'),
    ]

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Flag'
        verbose_name_plural = 'Flags'


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
class Photographer(index.Indexed, models.Model):
    # optional - we keep those in case but no longer needed
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone_regex = RegexValidator(
        regex=r'^0\d{10}$',
        message=(
            'Phone number must be entered in the format: "01234567890"; '
            '11 digits allowed.'
        )
    )
    phone_number = models.CharField(
        validators=[phone_regex], max_length=11, blank=True, null=True)

    #
    AGE_RANGE_CHOICES = [
        (0, 'unspecified'),
        (1, '18 and under'),
        (2, '19-25'),
        (3, '26-45'),
        (4, '46-65'),
        (5, '66 and over'),
    ]

    age_range = models.PositiveSmallIntegerField(
        choices=AGE_RANGE_CHOICES,
        default=0
    )

    GENDER_CHOICES = [
        (0, 'unspecified'),
        (1, 'other'),
        (2, 'female'),
        (3, 'male'),
    ]

    gender = models.PositiveSmallIntegerField(
        choices=GENDER_CHOICES,
        default=0
    )

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # ordering = ['last_name', 'first_name', 'email', 'phone_number']
        # unique_together = ['email', 'last_name', 'first_name']
        ordering = ['-created_at']

    def __str__(self):
        return 'Photographer #{}'.format(self.pk)

    # Django admin is the prefered interface to manage photographers
    panels = [
        # FieldPanel('first_name'),
        # FieldPanel('last_name'),
        # FieldPanel('email'),
        # FieldPanel('phone_number'),
        FieldPanel('age_range'),
        FieldPanel('gender'),
    ]

    # Django admin is the prefered interface to manage photographers
    search_fields = [
        # index.SearchField('first_name', partial_match=True),
        # index.SearchField('last_name', partial_match=True),
        # index.SearchField('email', partial_match=True),
        # index.SearchField('phone_number', partial_match=True),
        # index.SearchField('age_range', partial_match=True),
        # index.SearchField('gender', partial_match=True),
    ]

    @classmethod
    def get_age_range_from_age(cls, age=None):
        '''e.g. get_age_range_from_age(20) => 2 i.e. (2, '19-25')'''
        if isinstance(age, str):
            m = re.match(r'^\d+', age)
            if m:
                age = int(m.group(0))
            else:
                age = ''

        if age is None or age == '':
            return 0

        ret = 2
        while True:
            if ret >= len(cls.AGE_RANGE_CHOICES):
                break
            age_min = int(re.findall(
                r'^\d+', cls.AGE_RANGE_CHOICES[ret][1])[0])
            if age < age_min:
                break
            ret += 1
        ret -= 1

        return ret

    def get_str_from_age_range(self):
        return dict(self.AGE_RANGE_CHOICES).get(self.age_range, '')

    @classmethod
    def get_age_range_from_str(cls, age_range_str):
        '''19-25 => 2'''
        return {s: n for n, s in cls.AGE_RANGE_CHOICES}[age_range_str]

    def get_str_from_gender(self):
        return dict(self.GENDER_CHOICES).get(self.gender, '')


@register_snippet
class Photo(index.Indexed, models.Model):

    REVIEW_STATUS_SUBMITTING = -1
    REVIEW_STATUS_SUBMITTED = 0
    REVIEW_STATUS_PUBLIC = 1
    REVIEW_STATUS_ARCHIVED = 2
    REVIEW_STATUSES = (
        (REVIEW_STATUS_SUBMITTED, 'To be reviewed (not public)'),
        (REVIEW_STATUS_PUBLIC, 'Public'),
        (REVIEW_STATUS_ARCHIVED, 'Archived (not public)'),
        (REVIEW_STATUS_SUBMITTING, 'Incomplete submission'),
    )

    photographer = models.ForeignKey(
        Photographer,
        on_delete=models.SET_NULL,
        null=True, blank=True, default=None
    )

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

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    taken_year = models.IntegerField(
        'Year (photo content)', blank=True, null=True, default=None)
    taken_month = models.IntegerField(
        'Month (photo content)', blank=True, null=True, default=None)
    taken_day = models.IntegerField(
        'Day (photo content)', blank=True, null=True, default=None)

    location = models.PointField(blank=True, null=True)

    review_status = models.IntegerField(choices=REVIEW_STATUSES, default=0)

    subcategories = models.ManyToManyField(PhotoSubcategory)

    panels = [
        SnippetChooserPanel('photographer'),
        FieldPanel('review_status'),
        FieldPanel('number'),
        ImageChooserPanel('image'),
        FieldPanel('subcategories'),
        FieldPanel('description'),
        FieldPanel('comments'),
        FieldPanel('date'),
        FieldPanel('location'),
    ]

    search_fields = [
        index.FilterField('review_status'),
        index.FilterField('subcategories__pk'),
        # index.SearchField('subcategories__pk'),
        index.FilterField('photosubcategory_id'),
        index.FilterField('image_id'),
        index.SearchField('description', partial_match=True),
        #         index.RelatedFields('photographer', [
        #             index.SearchField('first_name', partial_match=True),
        #             index.SearchField('last_name', partial_match=True),
        #         ]),
    ]

    class Meta:
        ordering = ['-created_at']

#     def __init__(self, *args, **kwargs):
#         super(Photo, self).__init__(*args, **kwargs)
#         print(self.pk)

    def __str__(self):
        # TODO: find a better way to show pictures on the snippet list page
        # than embedding html tag here.
        return mark_safe('[{}] {}: {}<br>{}'.format(
            self.review_status_label,
            self.photographer, self.title,
            self.get_image_tag('height-50')
        ))

    @property
    def taken_month_name(self):
        from calendar import month_name
        ret = month_name[self.taken_month] if self.taken_month else ''
        return ret

    @property
    def review_status_label(self):
        ret = dict(self.REVIEW_STATUSES)[self.review_status]
        return ret

    @property
    def title(self):
        '''Derives a title from self.description'''
        ret = self.description or ''

        max_len = 50

        if len(ret) > max_len:
            # heuristics to keep smallest meaningful beginning of the desc.
            ret = re.sub(r'\(.*?\)', '', ret)
            ret = re.sub(r'( -|--).*$', '', ret)
            ret = re.sub(r'[.,;:].*$', '', ret)
            ret = re.sub(r'(([A-Z]\w*\b\s*){2,}).*$', r'\1', ret)
            ret = ret.strip()

            if len(ret) > max_len:
                # still too long, truncate and add the ellipsis
                ret = ret[:max_len] + '...'

        return ret

    def get_image_tag(self, specs='height-500'):
        '''
        Returns an html <image> tag for the related image.
        See Wagtail get_rendition_or_not_found() for valid specs.
        '''
        ret = ''

        if self.image:
            rendition = get_rendition_or_not_found(self.image, specs)
            # Remove height and width to keep things responsive.
            # they will be set by CSS.
            ret = re.sub(r'(?i)(height|width)=".*?"', '', rendition.img_tag())

        return ret

    def get_json_dic(self, imgspecs=None, geo_only=False):
        '''Returns a python dictionary representing this instance
        This dictionary will be converted into javascript by the web API
        '''
        p = self

        # TODO: should be dynamic, based on client (smaller for mobile devices)
        type_slug = 'photos'

        location = None
        if p.location:
            location = [p.location.y, p.location.x]

        if geo_only:
            ret = OrderedDict([
                ['id', str(p.pk)],
                ['type', type_slug],
                ['attributes', {
                    'location': location,
                }]
            ])
        else:
            ret = OrderedDict([
                ['id', str(p.pk)],
                ['type', type_slug],
                ['attributes', {
                    'title': p.title,
                    'description': p.description,
                    'location': location,
                    'image': self.get_image_tag(imgspecs),
                    # TODO: don't hard-code this!
                    'url': '/{}/{}'.format(type_slug, p.pk),
                    'taken_year': p.taken_year,
                    'taken_month': p.taken_month,
                    'taken_month_name': p.taken_month_name,
                    'taken_day': p.taken_day,
                    'created_at': p.created_at,
                }]
            ])

        return ret
