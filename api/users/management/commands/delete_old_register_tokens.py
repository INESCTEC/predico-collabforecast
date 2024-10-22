from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import OneTimeRegisterToken


class Command(BaseCommand):
    help = 'Delete old or expired registration tokens'

    def handle(self, *args, **kwargs):
        # Delete tokens that are either expired or already used
        now = timezone.now()
        old_tokens = OneTimeRegisterToken.objects.filter(
            expiration_time__lt=now  # Tokens that have expired
        ) | OneTimeRegisterToken.objects.filter(
            used=True  # Tokens that have already been used
        )

        # Count and delete the old tokens
        old_tokens_count = old_tokens.count()
        old_tokens.delete()

        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {old_tokens_count} old or expired tokens'))
