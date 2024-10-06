import uuid

from django.db import models

from .market_session import MarketSession


class MarketSessionChallenge(models.Model):
    class UseCase(models.TextChoices):
        WIND_FORECAST = 'wind_power'
        WIND_RAMP_FORECAST = 'wind_power_ramp'

    # Challenge ID
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    # User ID:
    user = models.ForeignKey(
        to="users.User",
        on_delete=models.CASCADE,
    )
    # Resource ID. At each session, the challenger (market maker) can create
    # challenges for the users to submit their forecasts (for his resources)
    resource = models.ForeignKey(
        to="users.UserResources",
        on_delete=models.CASCADE,
    )
    # Market session ID:
    market_session = models.ForeignKey(
        to=MarketSession,
        on_delete=models.CASCADE,
    )
    # Forecast use case for this bid:
    use_case = models.CharField(
        max_length=18,
        choices=UseCase.choices,
        default=UseCase.WIND_RAMP_FORECAST)
    # Forecast expected start datetime:
    start_datetime = models.DateTimeField(
        blank=False,
        null=False
    )
    # Forecast expected end datetime:
    end_datetime = models.DateTimeField(
        blank=False,
        null=False
    )
    # Forecast expected end datetime:
    target_day = models.DateField(
        blank=False,
        null=False
    )
    # Register date:
    registered_at = models.DateTimeField(
        auto_now_add=True
    )
    # Update date:
    updated_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        # the bidder should only have one bid for one specific session
        unique_together = ("market_session", "user", "resource")
        db_table = "market_session_challenge"
