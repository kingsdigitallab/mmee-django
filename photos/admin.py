from django.contrib.gis import admin
from .models import Photographer, PhotoSubcategory, Photo
from django.utils.safestring import mark_safe
from django.contrib.admin import SimpleListFilter
from django.contrib.gis.db import models
from mapwidgets.widgets import GooglePointFieldWidget


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


@admin.register(Photo)
# class PhotoAdmin(admin.OSMGeoAdmin):
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['id', 'photographer', 'title',
                    'review_status', 'created_at', 'admin_thumbnail']
    list_display_links = list_display

    list_filter = ['review_status', PhotoLocationFilter,
                   PhotoSubcategoriesFilter, PhotoImageFilter, ]

    search_fields = ['photographer__first_name',
                     'photographer__last_name', 'description']

    fieldsets = (
        ('Admin', {
            'fields': ('review_status', 'subcategories', 'comments')
        }),
        ('Related records', {
            # 'classes': ('collapse',),
            'fields': ('image', 'photographer',),
        }),
        ('Photo Properties', {
            # 'classes': ('collapse',),
            'fields': ('taken_year', 'taken_month', 'taken_day',
                       'description',
                       ),
        }),
        ('Location', {
            # 'classes': ('collapse',),
            'fields': ('location',),
        }),
    )

    filter_horizontal = ('subcategories',)

    formfield_overrides = {
        models.PointField: {"widget": GooglePointFieldWidget},
    }

    def admin_thumbnail(self, photo):
        return mark_safe(photo.get_image_tag('height-100'))
    admin_thumbnail.short_description = 'Thumbnail'

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
        "Mark selected photos as 'submitted'"

    actions = [action_status_public,
               action_status_archived, action_status_submitted]

#     def get_fields(self, request, obj=None):
#         fields = super().get_fields(request, obj)
#
#         if not is_moderator(request.user):
#             fields.remove('public')
#
#         return fields


def is_moderator(user):
    if user.is_superuser:
        return True

    return user.groups.filter(name='Moderators').exists()


@admin.register(Photographer)
class PhotographerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'age_range']
    list_filter = ['age_range']

    search_fields = ['first_name', 'last_name', 'email', 'phone_number']
