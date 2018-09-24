from django.contrib.gis import admin

from .models import MonumentType, Photo, Photographer


@admin.register(MonumentType)
class MonumentTypeAdmin(admin.ModelAdmin):
    list_display = ['title']


@admin.register(Photo)
class PhotoAdmin(admin.OSMGeoAdmin):
    filter_horizontal = ['monument_type']

    list_display = ['photographer', 'number', 'title', 'date']
    list_filter = ['photographer__age_range', 'monument_type__title']

    search_fields = ['photographer__first_name',
                     'photographer__last_name', 'title']

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)

        if not is_moderator(request.user):
            fields.remove('public')

        return fields


def is_moderator(user):
    if user.is_superuser:
        return True

    return user.groups.filter(name='Moderators').exists()


@admin.register(Photographer)
class PhotographerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'age_range']
    list_filter = ['age_range']

    search_fields = ['first_name', 'last_name', 'email', 'phone_number']
