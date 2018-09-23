# from django.conf import settings
from django.contrib import admin
from django.urls import path   # include, re_path
from .views import PhotoSearchView

admin.autodiscover()

urlpatterns = [
    path('', PhotoSearchView.as_view()),
]
