from django.db import models


class IndividualForecasts(models.Model):

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

    # User ID:
    user = models.ForeignKey(
        to="users.User",
        on_delete=models.CASCADE,
    )
    # Target Resource ID
    resource = models.ForeignKey(
        to="users.UserResources",
        on_delete=models.CASCADE,
    )
    # Forecast Horizon Timestamps:
    datetime = models.DateTimeField(
        blank=False,
        null=False
    )
    # Forecast Launch Time Timestamp:
    launch_time = models.DateTimeField(
        blank=False,
        null=False
    )
    # Forecast variable
    variable = models.CharField(
        max_length=5,
        choices=ForecastsVariable.choices,
        null=False,
        blank=False
    )
    # Time-series Value:
    value = models.FloatField(
        blank=False,
        null=False
    )
    # Insert date:
    registered_at = models.DateTimeField(blank=False)

    class Meta:
        db_table = "individual_forecasts"
        unique_together = ("user", "resource", "variable", "datetime")
