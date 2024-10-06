from django.db import models


class RawData(models.Model):

    class RawDataUnits(models.TextChoices):
        WATT = 'w', "Watt"
        KILO_WATT = 'kw', "Kilowatt"
        MEGA_WATT = 'mw', "Megawatt"

    # User ID:
    user = models.ForeignKey(
        to="users.User",
        on_delete=models.CASCADE,
    )
    # Resource ID (each user will have 1 bid per resource):
    resource = models.ForeignKey(
        to="users.UserResources",
        on_delete=models.CASCADE,
    )
    # Time-series Timestamp:
    datetime = models.DateTimeField(
        blank=False,
        null=False
    )
    # Time-series Value:
    value = models.FloatField(
        blank=False,
        null=False
    )
    # Time-series Unit:
    units = models.CharField(
        max_length=2,
        choices=RawDataUnits.choices,
        null=False,
        blank=False)

    # Insert date:
    registered_at = models.DateTimeField(blank=False)

    class Meta:
        db_table = "raw_data"
        unique_together = ("user", "resource", "datetime")
