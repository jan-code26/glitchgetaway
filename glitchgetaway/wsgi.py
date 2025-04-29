"""
WSGI config for glitchgetaway project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from django.core.management import call_command
from escape.models import Room

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glitchgetaway.settings')

application = get_wsgi_application()


try:
    call_command('migrate')
    if Room.objects.count() == 0:
        call_command('loaddata', 'escape_rooms.json')
        print("Rooms loaded.")
except Exception as e:
    print(f"Migration or loading error: {e}")

