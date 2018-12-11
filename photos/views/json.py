# from django.http import Http404
# from django.shortcuts import render
from ..models import Photo
from django.views import View
from django.http.response import JsonResponse
from photos.models import PhotoSubcategory
from collections import OrderedDict
from wagtail.search.query import MATCH_ALL
from wagtail.search.backends import get_search_backend
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage
from django.contrib.gis.geos.point import Point
from django.contrib.gis.db.models.functions import Distance
import time

# Our API complies with JSON API standard
# see https://jsonapi.org/format/
JSONAPI_VERSION = '1.0'

'''
Important notes about coordinates:
Django uses (long, lat) but leaflet uses (lat, long).
The conversion is done by the API, so it receieves and returns (lat, long).
'''
MAP_DEFAULT_CENTRE = '51.52,-0.03,12'

# mapping between ordering labels and the associated field used in
# QS.order_by()
QUERY_ORDER_NAME_FIELD = OrderedDict([
    ['newest', ['-taken_year', '-taken_month']],
    ['oldest', ['taken_year', 'taken_month']],
])
for name in QUERY_ORDER_NAME_FIELD:
    QUERY_ORDER_NAME_DEFAULT = name
    break


def get_search_query_from_request(request):
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
        'page': page,
        'view': request.GET.get('view', 'grid'),
        'perpage': request.GET.get('perpage', settings.ITEMS_PER_PAGE),
        'geo': request.GET.get('geo', MAP_DEFAULT_CENTRE),
    }

    return ret


class ApiPhotoSearchView(View):
    template_name = 'photos/search.html'
    model = Photo

    def get(self, request):
        return JsonResponse(self.search(request))

    def search(self, request):
        '''
        Search for Photos based on the request's query string.
        Returns a dictionary with results and metadata.
        Dictionary format follows JSON API standard.

        https://jsonapi-validator.herokuapp.com/
        https://jsonapi.org/format/#document-meta
        '''
        t0 = time.time()

        search_query = get_search_query_from_request(request)

        # Baseline query: get all live Photos with an image attached to them
        items = self.model.objects.filter(
            image__isnull=False,
            review_status=self.model.REVIEW_STATUS_PUBLIC
        )

        # filter by selected facets
        query_facets = search_query['facets']
        selected_facet_options = {}
        for facet_option in query_facets.split(';'):
            pair = facet_option.split(':')
            selected_facet_options[facet_option] = 1
            if pair[0] == 'cat':
                items = items.filter(subcategories__pk=pair[1])

        # ordering
        if search_query['order'] == 'nearest':
            # ['51.1', '1', 12] => [51.1, 1]
            center = [float(v) for v in search_query['geo'].split(',')]
            # lat, long -> long, lat
            center = Point(center[1], center[0], srid=4326)
            # https://stackoverflow.com/a/35896358/3748764
            items = items.annotate(
                distance=Distance('location', center)
            ).order_by('distance')
        else:
            items = items.order_by(
                *QUERY_ORDER_NAME_FIELD.get(
                    search_query['order'], ['-created_at']
                )
            )

        # text search (wagtail or haystack as a proxy to a search engine)
        s = get_search_backend()
        # returns a DatabaseSearchResults or similar Wagtail result class.
        # NOT a Django QuerySet
        items = s.search(search_query['phrase'] or MATCH_ALL, items)

        facets = self.get_facets_from_items(items, selected_facet_options)

        # Create response dictionary
        meta = OrderedDict([
            ['pagination', {}],
            ['query', search_query],
            ['qs', self.get_query_string(search_query)],
            ['debug', {}],
            ['facets', facets],
        ])

        # PLEASE keep this compatible with JSON API format!
        # jsonapi.org
        ret = OrderedDict([
            ['jsonapi', {'version': JSONAPI_VERSION}],
            ['meta', meta],
            ['data', items],
        ])

        # paginate the result and response
        self.paginate_response(ret, items, search_query, request)

        # serialise Photos into JSON-like dictionaries
        imgspecs = request.GET.get('imgspecs', 'height-500')
        ret['data'] = [
            item.get_json_dic(imgspecs=imgspecs)
            for item in ret['data']
        ]

        t1 = time.time()
        ret['meta']['debug'] = {
            'duration': t1 - t0
        }

        return ret

    def paginate_response(self, res, items, search_query, request):
        per_page = search_query['perpage']
        paginator = Paginator(items, per_page)
        try:
            page = paginator.page(search_query['page'])
        except EmptyPage:
            page = paginator.page(1)

        if 'links' not in res:
            res['links'] = {}
        links = [
            ['first', 1],
            ['last', paginator.num_pages],
            ['prev', page.number - 1],
            ['next', page.number + 1],
        ]
        link_query = {}
        link_query.update(search_query)
        import re
        base_url = re.sub(r'[?#].*$', '', request.build_absolute_uri())
        for k, link in links:
            if link < 1 or link > paginator.num_pages:
                link = None
            else:
                link_query.update({'page': link})
                link = base_url + '?' + self.get_query_string(link_query)
            res['links'][k] = link

        res['meta']['pagination'] = {
            'count': paginator.count,
            'per_page': per_page,
            'page': page.number,
            'pages': paginator.num_pages,
        }

        res['data'] = page.object_list

    def get_query_string(self, params):
        import urllib
        ret = '&'.join([
            ('%s=%s' % (
                urllib.parse.quote(akey, ','),
                urllib.parse.quote(str(aval), ',')
            ))
            for akey, aval
            in params.items()
            if aval
        ])
        return ret

    def get_facets_from_items(self, items, selected_facet_options):
        '''
        Returns a dictionary of facet and options from search results.

        items: result object returned by wagtail search()
        selected_facet_options: selected options
        '''
        facets = []
        # https://docs.wagtail.io/en/latest/topics/search/searching.html
        # #faceted-search
        # format: [(PK, COUNT), ...]
        options = items.facet('subcategories__pk')
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
                facet_name, sub[0]) in selected_facet_options

            ops.append([
                facet_name, sub[0], sub[1],
                options[sub[0]], selected
            ])

        return facets
