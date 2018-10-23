import json as pjson
from django import template
from wagtail.core.models import Site
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def get_site_root(context):
    # NB this returns a core.Page, not the implementation-specific model used
    # so object-comparison to self will return false as objects would differ
    ret = None

    site = getattr(context['request'], 'site', None)
    if not site:
        # no reference, let's get ANY site
        site = Site.objects.first()

    if site:
        ret = site.root_page

    return ret


@register.filter
def json(obj):
    '''convert python <obj> to a marked-safe, compact json string

    floats are round to 3 decimals

    {{ my_python_var|json }}

    '''
    return mark_safe(pjson.dumps(
        obj,
        separators=(',', ':'),
    ))


@register.simple_tag(takes_context=True)
def form_field(context, field, *args, **kwargs):
    '''
    Render a form field with the given attribute values.
    {% form_field FORM.FIELD ATTR="VALUE" ... %}
    e.g.
    {% form_field my_form.first_name class="form-control" placeholder="Bob" %}

    Note, _ are replaced with - in the attribute names.
    '''
    kwargs = kwargs or {}
    ret = field.as_widget(
        attrs={k.replace('_', '-'): v for k, v in kwargs.items()})
    return ret
