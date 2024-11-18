import uuid

from django.db import models


class MarketSessionSubmission(models.Model):
    class ForecastsVariable(models.TextChoices):
        Q05 = 'q05'
        Q10 = 'q10'
        Q20 = 'q20'
        Q30 = 'q30'
        Q40 = 'q40'
        Q50 = 'q50'
        Q60 = 'q60'
        Q70 = 'q70'
        Q80 = 'q80'
        Q90 = 'q90'
        Q95 = 'q95'
        POINT = "point"

    # Submission ID
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    # Market session Challenge ID:
    market_session_challenge = models.ForeignKey(
        to="market.MarketSessionChallenge",
        on_delete=models.CASCADE,
    )
    # User ID:
    user = models.ForeignKey(
        to="users.User",
        on_delete=models.CASCADE,
    )
    # Forecast variable
    variable = models.CharField(
        max_length=5,
        choices=ForecastsVariable.choices,
        null=False,
        blank=False)

    # Register date:
    registered_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "market_session_submission"
        unique_together = ("user",
                           "variable",
                           "market_session_challenge")


class MarketSessionSubmissionForecasts(models.Model):
    # Submission ID:
    submission = models.ForeignKey(
        to=MarketSessionSubmission,
        on_delete=models.CASCADE,
    )
    # Forecast lead-times timestamps:
    datetime = models.DateTimeField(
        blank=False,
        null=False
    )
    # Forecast lead-times values:
    value = models.FloatField(
        blank=False,
        null=False
    )
    # Register date:
    registered_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "market_session_submission_forecasts"
        unique_together = ("submission", "datetime")
