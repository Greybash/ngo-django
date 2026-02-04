from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile

class Command(BaseCommand):
    help = 'Create UserProfile for existing users'

    def handle(self, *args, **kwargs):
        for user in User.objects.all():
            UserProfile.objects.get_or_create(user=user)
            self.stdout.write(f'Created profile for {user.email}')
        
        self.stdout.write(self.style.SUCCESS('Successfully created all profiles'))