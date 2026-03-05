from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a default superuser from environment variables'

    def handle(self, *args, **options):
        username = os.environ.get('SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('SUPERUSER_EMAIL', 'admin@example.com')
        password = os.environ.get('SUPERUSER_PASSWORD')
        
        if not password:
            self.stdout.write(
                self.style.WARNING('SUPERUSER_PASSWORD not set in environment')
            )
            return
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(f'User "{username}" already exists')
            return
        
        User.objects.create_superuser(username, email, password)
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created superuser "{username}"')
        )