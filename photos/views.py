# Create your views here.

# from django.http import Http404
# from django.shortcuts import render
from .models import Photo
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView


class PhotoSearchView(ListView):
    template_name = 'photos/search.html'
    model = Photo

    def get_queryset(self):
        return self.model.objects.filter(image__isnull=False)[:7]


class PhotoDetailView(DetailView):
    template_name = 'photos/photo.html'
    model = Photo
