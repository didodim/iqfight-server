"""
WSGI config for iqfight project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os,sys
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PARENT_PATH = os.path.dirname(BASE_DIR)
sys.path.append(BASE_DIR)
sys.path.append(PARENT_PATH)
sys.path.append(os.path.join(BASE_DIR,"iqfight_app"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iqfight.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
