from .base import *

# Everything here must be provided through environment variables.

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
ALLOWED_HOSTS = [os.environ['DJANGO_ALLOWED_HOSTS']]

# Database configuration env variable must be provided
DATABASES = {
    'default': {
        'ENGINE': os.environ['DJANGO_DB_ENGINE'],
        'NAME': os.environ['DJANGO_DB_NAME'],
        'USER': os.environ['DJANGO_DB_USERNAME'],
        'PASSWORD': os.environ['DJANGO_DB_PASSWORD'],
        'HOST': os.environ['DJANGO_DB_HOST'],
        'PORT': os.environ['DJANGO_DB_PORT']
    }
}

# Enable Google Analytics
GOOGLE_ANALYTICS_JS_PROPERTY_ID = os.environ['GOOGLE_ANALYTICS_PROPERTY_ID']
