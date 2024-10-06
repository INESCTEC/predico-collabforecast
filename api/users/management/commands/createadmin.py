from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create a superuser and prompt for additional fields'

    def handle(self, *args, **options):
        User = get_user_model()
        email = input('Email: ')
        password = input('Password: ')
        password_ = input('Confirm password: ')
        if password != password_:
            self.stdout.write(self.style.ERROR('Passwords do not match'))
            return

        # Check if password is weak. Should have at least special character
        # and one uppercase letter. The user can override this check
        if not any(char.isupper() for char in password) or not any(char in "!@#$%^&*()-_+=~`[]{}|;:,.<>?/" for char in password): # noqa
            self.stdout.write(self.style.WARNING('Password is weak. It should have at least one uppercase letter and one special character'))  # noqa
            override = input('(y/n) Override password check: ').lower()
            if override != 'y':
                return

        is_session_manager = input('(y/n) Is session manager: ').lower()

        # Add any additional fields here
        extra_fields = {
            'is_session_manager': is_session_manager == "y"
        }

        # Use the custom UserManager to create the superuser
        User.objects.create_superuser(email=email, password=password,
                                      **extra_fields)

        self.stdout.write(self.style.SUCCESS(
            f'Superuser created successfully with email {email}'))
