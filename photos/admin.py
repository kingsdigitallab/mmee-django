from django.contrib.gis import admin
from .models import Photographer, PhotoSubcategory, Photo, PhotoFlag
from django.utils.safestring import mark_safe
from django.contrib.admin import SimpleListFilter
from django.contrib.gis.db import models
from mapwidgets.widgets import GooglePointFieldWidget
from django.urls.base import reverse
from django.utils.html import escape


@admin.register(PhotoFlag)
class PhotoFlagAdmin(admin.ModelAdmin):
    list_display = ['id', 'updated_at',
                    'created_at', 'closed', 'admin_thumbnail']
    list_display_links = list_display

    search_fields = ['flagger_comment', 'reviewer_comment']

    list_filter = ['closed']

    def admin_thumbnail(self, flag):
        return mark_safe(flag.photo.get_image_tag('height-100'))
    admin_thumbnail.short_description = 'Thumbnail'


@admin.register(PhotoSubcategory)
class PhotoSubcategoryAdmin(admin.ModelAdmin):
    list_display = ['category', 'label']
    list_display_links = ['label']
    search_fields = ['category__label', 'label']


class PhotoImageFilter(SimpleListFilter):
    title = 'Image'  # or use _('country') for translated title
    parameter_name = 'image'

    def lookups(self, request, model_admin):
        return [
            ('missing', 'image is missing'),
            ('exist', 'has an image'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'missing':
            return queryset.filter(image__isnull=True)
        if self.value() == 'exist':
            return queryset.filter(image__isnull=False)


class PhotoFlagFilter(SimpleListFilter):
    title = 'Inappropriateness'
    parameter_name = 'flag'

    def lookups(self, request, model_admin):
        return [
            ('unresolved', 'to be reviewed'),
            ('resolved', 'resolved'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'unresolved':
            return queryset.filter(flags__closed=False)
        if self.value() == 'resolved':
            return queryset.filter(flags__isnull=False).exclude(
                flags__closed=False
            )


class PhotoSubcategoriesFilter(SimpleListFilter):
    title = 'Subcategories'  # or use _('country') for translated title
    parameter_name = 'subcat'

    def lookups(self, request, model_admin):
        return [
            ('missing', 'uncategorised'),
            ('exist', 'categorised'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'missing':
            return queryset.filter(subcategories__isnull=True)
        if self.value() == 'exist':
            return queryset.filter(subcategories__isnull=False)


class PhotoLocationFilter(SimpleListFilter):
    title = 'Location'  # or use _('country') for translated title
    parameter_name = 'location'

    def lookups(self, request, model_admin):
        return [
            ('missing', 'location unspeficied'),
            ('exist', 'geolocated'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'missing':
            return queryset.filter(location__isnull=True)
        if self.value() == 'exist':
            return queryset.filter(location__isnull=False)


class PhotographerInline(admin.TabularInline):
    model = Photographer


class PhotoFlagInline(admin.StackedInline):
    model = PhotoFlag
    extra = 0
    verbose_name = 'User Flag'
    verbose_name_plural = 'User Flags'
    can_delete = False


def get_photographer_link(photo, link_text):
    ret = '<a href="{}">{}</a>'.format(
        reverse(
            "admin:photos_photographer_change",
            args=(photo.photographer.pk,)
        ),
        escape(link_text)
    )
    return mark_safe(ret)


@admin.register(Photo)
# class PhotoAdmin(admin.OSMGeoAdmin):
class PhotoAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'title', 'admin_inapproprieteness',
        'review_status', 'created_at', 'admin_thumbnail',
    ]
    list_display_links = [f for f in list_display if 'pher' not in f]

    list_filter = ['review_status', PhotoFlagFilter,
                   PhotoLocationFilter,
                   PhotoSubcategoriesFilter, PhotoImageFilter,
                   'photographer__gender', 'photographer__age_range'
                   ]

    search_fields = ['photographer__first_name',
                     'photographer__last_name', 'description']

    inlines = [PhotoFlagInline]

    fieldsets = (
        ('Status', {
            'fields': ('review_status', )
        }),
        ('Related records', {
            'fields': ('image', 'photographer',),
        }),
        ('Edited information', {
            'fields': (
                'subcategories',
                'comments'
            ),
        }),
        ('Submitted information', {
            'fields': (
                'taken_year', 'taken_month',  # 'taken_day',
                'description',
            ),
        }),
        ('Location', {
            'fields': ('location',),
        }),
    )

    filter_horizontal = ('subcategories',)

    formfield_overrides = {
        models.PointField: {'widget': GooglePointFieldWidget},
    }

    def admin_photographer_age_range(self, photo):
        ret = ''
        if photo.photographer:
            ret = photo.photographer.get_str_from_age_range()
            ret = get_photographer_link(photo, ret)
        return ret
    admin_photographer_age_range.short_description = 'Age'

    def admin_photographer_gender(self, photo):
        ret = ''
        if photo.photographer:
            ret = photo.photographer.get_str_from_gender()
            ret = get_photographer_link(photo, ret)
        return ret
    admin_photographer_gender.short_description = 'Gender'

    def admin_thumbnail(self, photo):
        return mark_safe(photo.get_image_tag('height-100'))
    admin_thumbnail.short_description = 'Thumbnail'

    def admin_inapproprieteness(self, photo):
        ret = ''
        open_flag_counts = photo.flags.filter(closed=False).count()
        if open_flag_counts:
            ret = 'Flagged as inappropriate'
        return ret
    admin_inapproprieteness.short_description = 'Inappropriate?'

    def action_status_public(modeladmin, request, queryset):
        queryset.update(review_status=Photo.REVIEW_STATUS_PUBLIC)
    action_status_public.short_description =\
        "Publish"

    def action_status_archived(modeladmin, request, queryset):
        queryset.update(review_status=Photo.REVIEW_STATUS_ARCHIVED)
    action_status_archived.short_description =\
        "Archive"

    def action_status_submitted(modeladmin, request, queryset):
        queryset.update(review_status=Photo.REVIEW_STATUS_SUBMITTED)
    action_status_submitted.short_description =\
        "Up for review"

    actions = [action_status_public,
               action_status_archived, action_status_submitted]


def is_moderator(user):
    if user.is_superuser:
        return True

    return user.groups.filter(name='Moderators').exists()


@admin.register(Photographer)
class PhotographerAdmin(admin.ModelAdmin):
    # list_display = ['first_name', 'last_name', 'age_range']
    list_display = ['pk', 'first_name', 'last_name', 'age_range']
    list_filter = ['age_range', 'gender']

    search_fields = ['first_name', 'last_name', 'email', 'phone_number', 'pk']
