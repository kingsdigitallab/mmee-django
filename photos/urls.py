# from django.conf import settings
from django.contrib import admin
from django.urls import path   # include, re_path
from photos.views.html import PhotoSearchView, PhotoDetailView
from photos.views.json import ApiPhotoSearchView

admin.autodiscover()

API_VERSION = '1.0'
API_ROOT = 'api/{}'.format(API_VERSION)

urlpatterns = [
    path('photos/', PhotoSearchView.as_view()),
    path('photos/<slug:pk>/', PhotoDetailView.as_view()),
    path(API_ROOT + '/photos/', ApiPhotoSearchView.as_view()),
    # path(API_ROOT + '/photos/<slug:pk>/', ApiPhotoDetailView.as_view()),
]
