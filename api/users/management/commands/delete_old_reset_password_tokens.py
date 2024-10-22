from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from users.models import PasswordResetRequest


class Command(BaseCommand):
    help = 'Delete password reset requests older than 24 hours'

    def handle(self, *args, **kwargs):
        threshold = timezone.now() - timedelta(hours=24)
        old_requests = PasswordResetRequest.objects.filter(created_at__lt=threshold)
        old_requests_count = old_requests.count()
        old_requests.delete()
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted '
                                             f'{old_requests_count} old password '
                                             f'reset requests'))
