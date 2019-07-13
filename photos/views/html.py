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
# from mapwidgets.widgets import GooglePointFieldWidget
from django.contrib.gis.forms.widgets import OSMWidget
from django import forms
from django.db import transaction
from wagtail.core.models import Page
from django.conf import settings


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
    '''
    Web Form for public users to report an issue with a photo
    '''

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

        context['moderation_page'] = Page.objects.filter(
            slug=settings.MODERATION_POLICY_PAGE_SLUG
        ).first()

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
        widget=forms.RadioSelect(),
        initial=0,
    )
    gender = ChoiceField(
        choices=Photographer.GENDER_CHOICES,
        widget=forms.RadioSelect(),
        initial=0,
    )
    gender_other = CharField(max_length=20, required=False)

    consent = BooleanField()

    class Meta:
        fields_required = [
            'taken_year',
            'author_focus_keywords',
            'author_reason',
        ]
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

        widgets = {
            'location': OSMWidget(dict(
                default_lon=-0.13,
                default_lat=51.5,
            )),
            'author_feeling_category': forms.RadioSelect(),
            # 'taken_month': forms.RadioSelect()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        fields_required = getattr(self.Meta, 'fields_required', [])
        for key in fields_required:
            self.fields[key].required = True


class PhotoCreateView(CreateView):
    template_name = 'photos/create.html'
    form_class = PhotoForm
    success_url = '/photos/created/'
    template_name_success = 'photos/created.html'

    def form_invalid(self, form):
        # TODO: remove this
        # print('INVALID')
        # print(self.request.FILES)
        # print(form.errors)
        return super().form_invalid(form)

    @transaction.atomic
    def form_valid(self, form):
        image_file = form.cleaned_data['image_file']

        # print(image_file.name)

        photographer = Photographer(
            age_range=form.cleaned_data['age_range'],
            gender_category=form.cleaned_data['gender'],
            gender_other=form.cleaned_data['gender_other'],
        )
        photographer.save()

        image = Image(
            title=image_file.name,
            file=image_file
        )
        image.save()

        photo = form.save()
        photo.image = image
        photo.photographer = photographer
        photo.save()

        self.request.session['reference_number'] = photo.reference_number

        return super().form_valid(form)
