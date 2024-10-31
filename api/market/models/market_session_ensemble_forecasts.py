import uuid

from django.db import models


class MarketSessionEnsemble(models.Model):
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
    class EnsembleModel(models.TextChoices):
        GBR = 'GBR'
        WEIGHTED_AVG = "weighted_avg"
        EQ_WEIGHTS = "eq_weights"
        LR = "LR"
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
    # Market session Challenge ID:
    model = models.CharField(
        max_length=20,
        choices=EnsembleModel.choices,
        null=False,
        blank=False
    )
    # Forecast variable
    variable = models.CharField(
        max_length=5,
        choices=ForecastsVariable.choices,
        null=False,
        blank=False
    )
    # Register date:
    registered_at = models.DateTimeField(
        auto_now_add=True
    )
    class Meta:
        db_table = "market_session_ensemble"
        unique_together = ("market_session_challenge", "model", "variable")


class MarketSessionEnsembleForecasts(models.Model):
    # Ensemble ID:
    ensemble = models.ForeignKey(
        to=MarketSessionEnsemble,
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
        db_table = "market_session_ensemble_forecasts"
        unique_together = ("ensemble", "datetime")


class MarketSessionRampAlerts(models.Model):
    # Challenge ID:
    challenge = models.ForeignKey(
        to="market.MarketSessionChallenge",
        on_delete=models.CASCADE,
    )
    # Forecast lead-times timestamps:
    datetime = models.DateTimeField(
        blank=False,
        null=False
    )
    # Ramp Detection Model ID:
    model = models.CharField(
        max_length=30,
        null=False,
        blank=False
    )
    # Alarm detection cluster id:
    cluster_id = models.IntegerField(
        blank=False,
        null=False
    )
    iqw = models.FloatField(
        blank=False,
        null=False
    )
    # Alarm detection consecutive count:
    consecutive_count = models.IntegerField(
        blank=False,
        null=False
    )
    # Reference quantiles:
    variability_quantiles = models.JSONField(
        blank=False,
        null=False
    )
    # Register date:
    registered_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "market_session_ramp_alerts"
        unique_together = ("challenge", "datetime")
