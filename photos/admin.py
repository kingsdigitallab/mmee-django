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


@admin.register(Photographer)
class PhotographerAdmin(admin.ModelAdmin):
    list_display = ['name', 'age_range']
    list_filter = ['age_range']
