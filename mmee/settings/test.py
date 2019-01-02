from .base import *  # noqa

DEBUG = True
TEMPLATES[0]['OPTIONS']['debug'] = True

SECRET_KEY = 'test'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache',
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
    },
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

SPATIALITE_LIBRARY_PATH = 'mod_spatialite'
