import warnings
from django.utils.deprecation import RemovedInDjango31Warning

from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3'
    }
}

# Shut down some deprecation warnings
warnings.simplefilter('default')
warnings.filterwarnings('ignore', category=RemovedInDjango31Warning)
