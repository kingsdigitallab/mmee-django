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
from django.core.paginator import Paginator

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
        'page': page
    }

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
            dict_response = self.get_queryset(request)
            ret = JsonResponse(dict_response)
        else:
            context['search_query'] =\
                get_search_query_from_request(request)
            ret = render(request, self.template_name, context)

        return ret


class ApiPhotoSearchView(View):
    template_name = 'photos/search.html'
    model = Photo

    def get(self, request):
        # JSON API standard format
        # https://jsonapi-validator.herokuapp.com/
        # https://jsonapi.org/format/#document-meta
        return JsonResponse(self.get_queryset(request))

    def get_queryset(self, request):
        search_query = get_search_query_from_request(request)

        # Baseline query: get all Photos with an image attached to them
        items = self.model.objects.filter(
            image__isnull=False
        )

        # filter by selected facets
        query_facets = search_query['facets']
        selected_facet_option = {}
        for facet_option in query_facets.split(';'):
            pair = facet_option.split(':')
            selected_facet_option[facet_option] = 1
            if pair[0] == 'cat':
                items = items.filter(subcategories__pk=pair[1])

        # ordering
        items = items.order_by(QUERY_ORDER_NAME_FIELD.get(
            search_query['order'], '-date'))

        # text search (wagtail or haystack as a proxy to a search engine)
        s = get_search_backend()
        # returns a DatabaseSearchResults or similar Wagtail result class.
        # NOT a Django QuerySet
        items = s.search(search_query['phrase'] or MATCH_ALL, items)

        # faceting
        if 1:
            facets = []
            # https://docs.wagtail.io/en/latest/topics/search/searching.html
            # #faceted-search
            # format: [(PK, COUNT), ...]
            options = items.facet('subcategories__pk')
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

        meta = OrderedDict([
            ['pagination', {}],
            ['query', search_query],
            ['qs', self.get_query_string(search_query)],
            ['facets', facets],
        ])

        ret = OrderedDict([
            ['jsonapi', {'version': JSONAPI_VERSION}],
            ['meta', meta],
            ['data', items],
        ])

        self.paginate_response(ret, items, search_query, request)

        ret['data'] = [
            item.get_json_dic()
            for item in ret['data']
        ]

        return ret

    def paginate_response(self, res, items, search_query, request):
        per_page = settings.ITEMS_PER_PAGE
        paginator = Paginator(items, per_page)
        page = paginator.page(search_query['page'])

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
        base_url = request.path
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
