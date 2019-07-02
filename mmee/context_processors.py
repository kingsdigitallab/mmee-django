from django.conf import settings


def project_settings(request):

    ret = {
        name: getattr(settings, name)
        for name
        in settings.SETTINGS_VARS_IN_CONTEXT
    }

    return ret
