from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS.extend([
    'django_extensions',
    'debug_toolbar',
])

MIDDLEWARE.extend([
    'debug_toolbar.middleware.DebugToolbarMiddleware',
])

# Default settings for a PostgreSQL database are provided. You
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DJANGO_DB_ENGINE',
                                 default='django.db.backends.postgresql_psycopg2'),
        'NAME': os.environ.get('DJANGO_DB_NAME', default='sqds_local'),
        'USER': os.environ.get('DJANGO_DB_USERNAME', default='sqds_local'),
        'PASSWORD': os.environ.get('DJANGO_DB_PASSWORD', default=''),
        'HOST': os.environ.get('DJANGO_DB_HOST', default='localhost'),
        'PORT': os.environ.get('DJANGO_DB_PORT', default=5432),
    }
}


# noinspection PyUnusedLocal
def show_toolbar(request):
    return True


USE_DEBUG_TOOLBAR = True
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': 'sqdssite.settings.local.show_toolbar'
}

META_SITE_PROTOCOL = 'http'
