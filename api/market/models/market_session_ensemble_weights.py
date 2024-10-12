from django.db import models


class MarketSessionEnsembleWeights(models.Model):
    # Ensemble ID:
    ensemble = models.ForeignKey(
        to="MarketSessionEnsemble",
        on_delete=models.CASCADE,
    )
    # Forecaster user ID:
    user = models.ForeignKey(
        to="users.User",
        on_delete=models.CASCADE,
    )
    # Contribution value:
    value = models.FloatField(
        blank=False,
        null=False
    )
    # Register date:
    registered_at = models.DateTimeField(
        auto_now_add=True
    )
    class Meta:
        db_table = "market_session_ensemble_weights"
        unique_together = ("ensemble", "user")
