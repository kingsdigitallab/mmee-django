import json as pjson
from django import template
from wagtail.core.models import Site
from django.utils.safestring import mark_safe
from django.template import loader

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
    context = {}
    for var_name in ['label']:
        val = kwargs.get(var_name, None)
        if var_name in kwargs:
            del kwargs[var_name]
        context[var_name] = val

    attributes = kwargs or {}
    attributes.update({
        'autocomplete': 'off',
    })

    if 'class' not in attributes:
        attributes['class'] = ''

    attributes['class'] += ' form-control'

    field_html = field.as_widget(
        attrs={k.replace('_', '-'): v.strip() for k, v in attributes.items()}
    )

    template = loader.get_template('mmee/form_field.html')
    context['field'] = field_html
    context['errors'] = field.errors
    ret = template.render(context)

    # print(ret)

    return ret
