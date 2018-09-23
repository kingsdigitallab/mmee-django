# Create your views here.

# from django.http import Http404
# from django.shortcuts import render
from .models import Photo
from django.views.generic.list import ListView


class PhotoSearchView(ListView):
    template_name = 'photos/search.html'
    model = Photo
