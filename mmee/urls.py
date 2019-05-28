from django.urls import include, re_path, path
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from django.contrib import admin
from django.conf import settings
from wagtail.admin import urls as wagtailadmin_urls
from kdl_ldap.signal_handlers import \
    register_signal_handlers as kdl_ldap_register_signal_hadlers
import os.path

kdl_ldap_register_signal_hadlers()

admin.autodiscover()

urlpatterns = [
    path('taggit/', include('taggit_selectize.urls')),
    path('admin/', admin.site.urls),

    re_path('wagtail/', include(wagtailadmin_urls)),

    # re_path('documents/', include('wagtail.documents.urls')),

    path('', include('photos.urls')),
    # path('search/', include('haystack.urls')),

    # we temporarily by pass wagtail to show search interface on home page
    # nest increment we can implement search with proper wagtail page
    path('', RedirectView.as_view(url='/photos/', permanent=False)),

    re_path('', include('wagtail.core.urls')),

]

# -----------------------------------------------------------------------------
# Django Debug Toolbar URLS
# -----------------------------------------------------------------------------
try:
    if settings.DEBUG:
        import debug_toolbar
        urlpatterns = [
            re_path(r'^__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
except ImportError:
    pass

# -----------------------------------------------------------------------------
# Static file DEBUGGING
# -----------------------------------------------------------------------------
if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(
        settings.MEDIA_URL + 'images/',
        document_root=os.path.join(settings.MEDIA_ROOT, 'images')
    )
#     urlpatterns += [
#         re_path(r'^favicon\.ico$',
#           RedirectView.as_view(
#               url=settings.STATIC_URL + 'myapp/images/favicon.ico'))
#     ]
