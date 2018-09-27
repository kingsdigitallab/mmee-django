# Create your views here.

# from django.http import Http404
# from django.shortcuts import render
from .models import Photo
from django.views import View
from django.views.generic.detail import DetailView
from wagtail.images.shortcuts import get_rendition_or_not_found
import re
from django.http.response import JsonResponse
from django.shortcuts import render


class PhotoSearchView(View):
    template_name = 'photos/search.html'
    model = Photo

    def get(self, request):
        format = request.GET.get('format', 'html').lower()

        context = {}

        if format in ['js', 'json']:
            params = {}
            qs = self.get_queryset(request, params)
            context = {
                'photos': [
                    self._get_dict_from_photo(photo)
                    for photo in qs
                ],
                'qs': self.get_query_string(params)
            }
            ret = JsonResponse(context)
        else:
            context['search_query'] =\
                self.get_search_query_from_request(request)
            ret = render(request, self.template_name, context)

        return ret

    def _get_dict_from_photo(self, photo):
        image_tag = ''

        if photo.image:
            rendition = get_rendition_or_not_found(photo.image, 'height-500')
            image_tag = rendition.img_tag({'height': '', 'width': ''})
            image_tag = re.sub(r'(height|width)=".*?"', '', image_tag)

        p = photo

        ret = {
            'pk': p.pk,
            'title': p.title,
            'description': p.description,
            'location': [p.location.y, p.location.x] if p.location else None,
            'image': image_tag,
            # TODO: don't hard-code this!
            'url': '/photos/{}'.format(p.pk),
            'date': p.date.strftime('%B %Y'),
        }

        return ret

    def get_queryset(self, request, params=None):
        ret = self.model.objects.filter(
            image__isnull=False
        )

        search_query = self.get_search_query_from_request(request)

        if search_query['phrase']:
            ret = ret.filter(description__icontains=search_query['phrase'])
            # from wagtail.search.backends import get_search_backend
            # s = get_search_backend()
            # ret = s.search(search_query['phrase'], fields=['description'])
            # ret = ret.search(phrase, fields=['description'])

        order_fields = {
            'newest': '-date',
            'oldest': 'date'
        }
        ret = ret.order_by(order_fields.get(search_query['order'], '-date'))

        if params is not None:
            params.update(search_query)

        return ret

    def get_search_query_from_request(self, request):
        ret = {
            'phrase': request.GET.get('phrase', ''),
            'order': request.GET.get('order', 'newest')
        }

        return ret

    def get_query_string(self, params):
        import urllib
        ret = '&'.join([
            ('%s=%s' % (
                urllib.parse.quote(akey, ','),
                urllib.parse.quote(aval, ',')
            ))
            for akey, aval
            in params.items()
        ])
        return ret


class PhotoDetailView(DetailView):
    template_name = 'photos/photo.html'
    model = Photo

    def get(self, request, *args, **kwargs):
        ret = super(PhotoDetailView, self).get(request, *args, **kwargs)
        self.extra_context = {
            'phrase': request.GET.get('phrase', '')
        }
        return ret
