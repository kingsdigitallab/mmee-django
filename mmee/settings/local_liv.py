from .base import *  # noqa

ALLOWED_HOSTS = ['mmee.kdl.kcl.ac.uk']

INTERNAL_IPS = INTERNAL_IPS + ['']

DATABASES = {
    'default': {
        'ENGINE': db_engine,
        'NAME': 'app_mmee_liv',
        'USER': 'app_mmee',
        'PASSWORD': '',
        'HOST': ''
    },
}

SECRET_KEY = ''
