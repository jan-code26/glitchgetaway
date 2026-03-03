import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glitchgetaway.settings')

application = get_wsgi_application()

# Auto-run migrations and seed rooms on first deploy
try:
    from django.core.management import call_command
    from escape.models import Room

    call_command('migrate')

    if Room.objects.count() == 0:
        call_command('loaddata', 'escape_rooms.json')
        print("Rooms loaded from fixture.")
except Exception as e:
    print(f"Migration or loading error: {e}")
