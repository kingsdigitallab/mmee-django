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
from photos.models import PhotoSubcategory


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
                'qs': self.get_query_string(params),
                'facets': self.facets
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
        self.facets = []

        ret = self.model.objects.filter(
            image__isnull=False
        )

        query_facets = request.GET.get('facets', '')
        for option in query_facets.split(';'):
            pair = option.split(':')
            if pair[0] == 'cat':
                ret = ret.filter(subcategories__pk=pair[1])

        search_query = self.get_search_query_from_request(request)

        if 1 or search_query['phrase']:
            from wagtail.search.backends import get_search_backend
            s = get_search_backend()
            ret = s.search(search_query['phrase'] or 'a', ret)

            # ret = ret.filter(description__icontains=search_query['phrase'])

        if 1:
            options = ret.facet('subcategories__pk')
            subs = PhotoSubcategory.objects.filter(
                pk__in=[option for option in options.keys()]).values_list(
                    'pk', 'label', 'category__label'
            ).order_by('category__label', 'label')

            cat = None
            ops = []
            for sub in subs:
                facet = sub[2]

                if facet != cat:
                    cat = facet
                    ops = []
                    self.facets.append([facet, ops])

                ops.append(['cat', sub[0], sub[1], options[sub[0]], 0])

            # print(self.facets)

        # sorting (TODO: this work-around is bad, we need to use Haystack
        # directly instead)
        ret = self.model.objects.filter(pk__in=[r.pk for r in ret])

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
