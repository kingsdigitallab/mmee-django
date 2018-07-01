from django.contrib.gis import admin

from .models import Photo, Photographer


@admin.register(Photo)
class PhotoAdmin(admin.OSMGeoAdmin):
    list_display = ['photographer', 'number', 'title', 'date']
    list_filter = ['photographer__age_range']


@admin.register(Photographer)
class PhotographerAdmin(admin.ModelAdmin):
    list_display = ['name', 'age_range']
    list_filter = ['age_range']
