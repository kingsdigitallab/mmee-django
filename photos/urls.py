# from django.conf import settings
from django.contrib import admin
from django.urls import path   # include, re_path
from photos.views.html import PhotoSearchView, PhotoDetailView, PhotoCreateView
from photos.views.json import ApiPhotoSearchView
from django.views.generic.base import TemplateView

admin.autodiscover()

API_VERSION = '1.0'
API_ROOT = 'api/{}'.format(API_VERSION)

urlpatterns = [
    path('photos/', PhotoSearchView.as_view()),
    path('photos/create/', PhotoCreateView.as_view()),
    path('photos/created/', TemplateView.as_view(
        template_name='photos/created.html')),
    path('photos/<slug:pk>/', PhotoDetailView.as_view(), name='photo-view'),
    path(API_ROOT + '/photos/', ApiPhotoSearchView.as_view()),
    # path(API_ROOT + '/photos/<slug:pk>/', ApiPhotoDetailView.as_view()),
]
