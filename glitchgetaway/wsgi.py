import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glitchgetaway.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# 🔥 After Django is fully ready, then you can use models safely
try:
    from django.core.management import call_command
    from escape.models import Room

    call_command('migrate')

    if Room.objects.count() == 0:
        call_command('loaddata', 'escape_rooms.json')
        print("Rooms loaded from fixture.")
except Exception as e:
    print(f"Migration or loading error: {e}")
