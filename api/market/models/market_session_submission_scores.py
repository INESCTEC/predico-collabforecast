from django.db import models
from ..models.market_session_submission import MarketSessionSubmission


class MarketSessionSubmissionScores(models.Model):
    class ScoreMetrics(models.TextChoices):
        PINBALL = 'pinball'
        MAE = "mae"
        RMSE = "rmse"
    # Submission ID:
    submission = models.ForeignKey(
        to=MarketSessionSubmission,
        on_delete=models.CASCADE,
    )
    # Metric name:
    metric = models.CharField(
        max_length=10,
        choices=ScoreMetrics.choices,
        null=False,
        blank=False
    )
    # Metric value:
    value = models.FloatField(
        blank=False,
        null=False
    )
    # Register date:
    registered_at = models.DateTimeField(
        auto_now_add=True
    )
    class Meta:
        db_table = "market_session_submission_scores"
        unique_together = ("submission",
                           "metric")
