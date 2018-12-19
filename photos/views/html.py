# from django.http import Http404
# from django.shortcuts import render
from ..models import Photo
from photos.views.json import get_search_query_from_request
from django.views.generic.detail import DetailView
from django.views.generic.base import TemplateView
from django.forms.fields import (
    ImageField, BooleanField,
    CharField, ChoiceField
)
from django.views.generic.edit import CreateView
from wagtail.images.models import Image
from django.forms import ModelForm
from photos.models import PhotoFlag, Photographer
from django.core.exceptions import ValidationError


class PhotoSearchView(TemplateView):
    '''We don't inherit from Django ListView
    because the front-end uses json api to search without page reload.
    '''
    template_name = 'photos/search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = get_search_query_from_request(self.request)
        return context


class PhotoFlagForm(ModelForm):

    class Meta:
        model = PhotoFlag
        fields = [
            'flagger_comment',
        ]

    def clean_flagger_comment(self):
        ret = self.cleaned_data['flagger_comment']
        if ret == 'test':
            # for design purpose, easy way to see errors on page
            ret = ''
        if ret == 'test2':
            raise ValidationError(
                'A test error message, not related to a field'
            )
        return ret


class PhotoDetailView(DetailView):
    template_name = 'photos/photo.html'
    model = Photo

    def dispatch(self, *args, **kwargs):
        '''Init flag data/form each time we process a new request'''
        self.form_flag = PhotoFlagForm()
        self.photo_flag = None
        return super(PhotoDetailView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['phrase'] = self.request.GET.get('phrase', '')

        # a form for the user to flag a photo
        context['form_flag'] = self.form_flag
        # a new, saved PhotoFlag just posted by the user, None otherwise
        context['photo_flag'] = self.photo_flag

        return context

    def post(self, request, *args, **kwargs):
        '''The user posts a comment about photo being inappropriate'''
        photo = self.get_object()

        photo_flag = PhotoFlag(photo=photo)
        form_flag = PhotoFlagForm(request.POST, instance=photo_flag)

        if form_flag.is_valid():
            self.photo_flag = form_flag.save()

        self.form_flag = form_flag

        # this will call get_context_data()
        ret = self.get(request, *args, **kwargs)

        return ret


class PhotoForm(ModelForm):
    image_file = ImageField()

    age_range = ChoiceField(
        choices=Photographer.AGE_RANGE_CHOICES,
    )
    gender = ChoiceField(
        choices=Photographer.GENDER_CHOICES,
    )
    gender_other = CharField(max_length=20, required=False)

    consent = BooleanField()

    class Meta:
        model = Photo
        fields = [
            'image_file',
            'taken_year', 'taken_month',
            'location',
            # TODO: split into three inputs?
            'author_focus_keywords',
            'author_feeling_category',
            'author_feeling_keywords',
            'author_reason',
            # 'photographer__age_range',
            'age_range',
            # 'photographer__gender',
            'gender',
            # 'photographer__gender_other',
            'gender_other',
            'consent',
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
