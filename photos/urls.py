# from django.conf import settings
from django.contrib import admin
from django.urls import path   # include, re_path
from .views import PhotoSearchView, PhotoDetailView

admin.autodiscover()

urlpatterns = [
    path('', PhotoSearchView.as_view()),
    path('<slug:pk>/', PhotoDetailView.as_view()),
]
