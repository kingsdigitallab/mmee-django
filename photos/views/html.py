# from django.http import Http404
# from django.shortcuts import render
from ..models import Photo
from photos.views.json import get_search_query_from_request
from django.views.generic.detail import DetailView
from django.views.generic.base import TemplateView
from django.forms.fields import ImageField, BooleanField
from django.views.generic.edit import CreateView
from wagtail.images.models import Image
from django.forms import ModelForm


class PhotoSearchView(TemplateView):
    '''We don't inherit from Django ListView
    because the front-end uses json api to search without page reload.
    '''
    template_name = 'photos/search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = get_search_query_from_request(self.request)
        return context


class PhotoDetailView(DetailView):
    template_name = 'photos/photo.html'
    model = Photo

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['phrase'] = self.request.GET.get('phrase', '')
        return context


class PhotoForm(ModelForm):
    image_file = ImageField()
    consent = BooleanField()

    class Meta:
        model = Photo
        fields = [
            'image_file',
            'taken_year', 'taken_month', 'description',
            'consent'
        ]


class PhotoCreateView(CreateView):
    template_name = 'photos/create.html'
    form_class = PhotoForm
    success_url = '/photos/created/'

    def form_invalid(self, form):
        # TODO: remove this
        print('INVALID')
        print(self.request.FILES)
        print(form.errors)
        return super().form_invalid(form)

    def form_valid(self, form):
        image_file = form.cleaned_data['image_file']
        image = Image(
            title=image_file.name,
            file=image_file
        )
        image.save()

        photo = form.save()
        photo.image = image
        photo.save()

        print('New photo #', photo.pk, 'new image #', image.pk)
        return super().form_valid(form)
