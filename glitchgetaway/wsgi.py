"""
WSGI config for glitchgetaway project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

from escape.models import \
    Room

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glitchgetaway.settings')

application = get_wsgi_application()

try:
    from django.core.management import call_command
    call_command('migrate')
except Exception as e:
    print(f"Migration failed: {e}")

# Load initial rooms from fixture if none exist
try:
    if Room.objects.count() == 0:
        from django.core.management import call_command
        call_command('loaddata', 'escape_rooms.json')
        print("Rooms loaded from fixture.")
except Exception as e:
    print(f"Fixture loading failed: {e}")
