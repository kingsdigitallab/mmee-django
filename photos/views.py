# Create your views here.

# from django.http import Http404
# from django.shortcuts import render
from .models import Photo
from django.views import View
from django.views.generic.detail import DetailView
from django.http.response import JsonResponse
from django.shortcuts import render
from photos.models import PhotoSubcategory
from collections import OrderedDict
from wagtail.search.query import MATCH_ALL
from wagtail.search.backends import get_search_backend
from django.conf import settings
import math

# Our API complies with JSON API standard
# see https://jsonapi.org/format/
JSONAPI_VERSION = '1.0'

# mapping between ordering labels and the associated field used in
# QS.order_by()
QUERY_ORDER_NAME_FIELD = OrderedDict([
    ['newest', '-date'],
    ['oldest', 'date'],
])
for name in QUERY_ORDER_NAME_FIELD:
    QUERY_ORDER_NAME_DEFAULT = name
    break


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
        format = request.GET.get('format', 'html').lower()

        context = {}

        if format in ['js', 'json']:
            # JSON API standard format
            # https://jsonapi-validator.herokuapp.com/
            # https://jsonapi.org/format/#document-meta
            qs, meta = self.get_queryset(request)
            context = OrderedDict([
                ['jsonapi', JSONAPI_VERSION],
                ['meta', meta],
                ['data', [
                    photo.get_json_dic()
                    for photo in qs
                ]],
            ])
            ret = JsonResponse(context)
        else:
            context['search_query'] =\
                self.get_search_query_from_request(request)
            ret = render(request, self.template_name, context)

        return ret

    def get_queryset(self, request):
        search_query = self.get_search_query_from_request(request)

        # Baseline query: get all Photos with an image attached to them
        ret = self.model.objects.filter(
            image__isnull=False
        )

        # filter by selected facets
        query_facets = search_query['facets']
        selected_facet_option = {}
        for facet_option in query_facets.split(';'):
            pair = facet_option.split(':')
            selected_facet_option[facet_option] = 1
            if pair[0] == 'cat':
                ret = ret.filter(subcategories__pk=pair[1])

        # ordering
        ret = ret.order_by(QUERY_ORDER_NAME_FIELD.get(
            search_query['order'], '-date'))

        # text search (wagtail or haystack as a proxy to a search engine)
        s = get_search_backend()
        # returns a DatabaseSearchResults or similar Wagtail result class.
        # NOT a Django QuerySet
        ret = s.search(search_query['phrase'] or MATCH_ALL, ret)

        # faceting
        if 1:
            facets = []
            # https://docs.wagtail.io/en/latest/topics/search/searching.html
            # #faceted-search
            # format: [(PK, COUNT), ...]
            options = ret.facet('subcategories__pk')
            # print(options)
            subs = PhotoSubcategory.objects.filter(
                pk__in=[option for option in options.keys()]
            ).values_list(
                'pk', 'label', 'category__label'
            ).order_by('category__label', 'label')

            cat = None
            ops = []
            facet_name = 'cat'
            for sub in subs:
                facet = sub[2]

                if facet != cat:
                    cat = facet
                    ops = []
                    facets.append([facet, ops])

                selected = '{}:{}'.format(
                    facet_name, sub[0]) in selected_facet_option

                ops.append([
                    facet_name, sub[0], sub[1],
                    options[sub[0]], selected
                ])

            # print(self.facets)

        # pagination
        per_page = settings.ITEMS_PER_PAGE
        count = ret.count()
        num_pages = math.ceil(1.0 * count / per_page)

        page = search_query['page']
        if page > num_pages:
            page = num_pages
        search_query['page'] = page

        meta = OrderedDict([
            ['pagination', {
                'count': count,
                'per_page': per_page,
                'page': page,
                'pages': num_pages,
            }],
            ['query', search_query],
            ['qs', self.get_query_string(search_query)],
            ['facets', facets],
        ])

        ret = ret[(page - 1) * per_page:page * per_page]

        return ret, meta

    def get_search_query_from_request(self, request):
        try:
            page = int(request.GET.get('page', 1))
        except ValueError:
            page = 1
        if page < 1:
            page = 1
        ret = {
            'phrase': request.GET.get('phrase', ''),
            'order': request.GET.get('order', QUERY_ORDER_NAME_DEFAULT),
            'facets': request.GET.get('facets', ''),
            'page': page
        }

        return ret

    def get_query_string(self, params):
        import urllib
        ret = '&'.join([
            ('%s=%s' % (
                urllib.parse.quote(akey, ','),
                urllib.parse.quote(str(aval), ',')
            ))
            for akey, aval
            in params.items()
        ])
        return ret
