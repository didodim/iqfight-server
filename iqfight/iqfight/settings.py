"""
Django settings for iqfight project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os,sys
from inspect import trace

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR,"iqfight"))
sys.path.append(os.path.join(BASE_DIR,"iqfight","iqfight_app"))
LOG_DIR = os.path.join(BASE_DIR,"log")
try:
    os.mkdir(LOG_DIR)
except:
    pass
LOG_FILE = os.path.join(LOG_DIR,'log.txt')



# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '!p1%kqh^pez46f&t&0u)1c2-)9cn5*oy051o1ilzm_01*+hfc('

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'iqfight_app',
    'south'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
#    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'iqfight.urls'

WSGI_APPLICATION = 'iqfight.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': "iqfight",
        'USER': 'iqfight',                      # Not used with sqlite3.
        'PASSWORD': 'iqfight',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '', 
        'ATOMIC_REQUESTS':True
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Sofia'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
MEDIA_ROOT = os.path.join(BASE_DIR,"media")
MEDIA_URL = '/media/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {'format':'[%(levelname)s] %(asctime)s %(module)s: %(message)s'},
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'views':{
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE,
            'formatter': 'verbose',
            'maxBytes': 1048576,
            'backupCount': 3,
            }
    },
    'loggers': {
        'django.request': {
            'handlers': ['views'],
            'level': 'ERROR',
            'propagate': True,
        },
        'iqfight.iqfight_app.views':{
            'handlers': ['views'],
            'level': 'DEBUG',
            'propagate': True
            },
    }
}
import traceback
from django.utils import log
try:
    log.dictConfig(LOGGING)
except:
    print traceback.format_exc()
