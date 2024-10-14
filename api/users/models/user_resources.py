import uuid

from django.db import models


class UserResources(models.Model):
    class Timezones(models.TextChoices):
        BELGIUM = 'Europe/Brussels'
        PORTUGAL = 'Europe/Lisbon'
        UK = 'Europe/London'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        to="users.User",
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        max_length=64,
        null=False,
    )
    # local tz for this resource
    # (reference to created start/end datetime of forecast range):
    timezone = models.CharField(
        max_length=64,
        choices=Timezones.choices,
        blank=False,
        null=False
    )
    # Register date:
    registered_at = models.DateTimeField(auto_now_add=True, blank=True)
    # Update date:
    updated_at = models.DateTimeField(auto_now=True, blank=True)

    def __str__(self):
        return f'#{self.pk}: {self.user}, {self.name}'

    class Meta:
        unique_together = ("user", "name")
        db_table = 'user_resources'
