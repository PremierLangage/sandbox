*"""
WSGI config for pl_sandbox project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os, sys

from django.core.wsgi import get_wsgi_application

path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if path not in sys.path:
    sys.path.append(path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pl_sandbox.settings")

application = get_wsgi_application()
