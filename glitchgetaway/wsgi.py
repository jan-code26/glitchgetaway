import os
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glitchgetaway.settings')

application = get_wsgi_application()
application = WhiteNoise(application, root=os.path.join(BASE_DIR, 'staticfiles'))

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
