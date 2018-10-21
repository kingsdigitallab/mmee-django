# from django.http import Http404
# from django.shortcuts import render
from ..models import Photo
from django.views import View
from django.shortcuts import render
from photos.views.json import get_search_query_from_request
from django.views.generic.detail import DetailView


class PhotoDetailView(DetailView):
    template_name = 'photos/photo.html'
    model = Photo

    def get(self, request, *args, **kwargs):
        ret = super(PhotoDetailView, self).get(request, *args, **kwargs)
        self.extra_context = {
            'phrase': request.GET.get('phrase', '')
        }
        return ret


class PhotoSearchView(View):
    template_name = 'photos/search.html'
    model = Photo

    def get(self, request):
        context = {}

        context['search_query'] = get_search_query_from_request(request)
        return render(request, self.template_name, context)
