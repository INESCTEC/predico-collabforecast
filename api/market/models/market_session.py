from django.db import models


class MarketSession(models.Model):

    class MarketStatus(models.TextChoices):
        OPEN = 'open'          # Session open (accepts challenges)
        CLOSED = 'closed'      # Session closed (no challenges)
        RUNNING = 'running'    # Session being executed (no challenges)
        FINISHED = 'finished'  # Session finished (no challenges)

    id = models.AutoField(
        primary_key=True
    )
    # Datetime at which session was opened (bid placement time)
    open_ts = models.DateTimeField(
        auto_now_add=True,
        blank=False,
        null=False,
    )
    # Datetime at which session was closed (gate closure time)
    close_ts = models.DateTimeField(
        blank=True,
        null=True,
        default=None
    )
    # Datetime at which session launched (market run start)
    launch_ts = models.DateTimeField(
        blank=True,
        null=True,
        default = None
    )
    # Datetime at which session finished (market run ended)
    finish_ts = models.DateTimeField(
        blank=True,
        null=True,
        default=None
    )
    # Session status (updated during market processes)
    status = models.CharField(
        max_length=10,
        choices=MarketStatus.choices,
        default=MarketStatus.OPEN,
        null=False,
    )

    class Meta:
        unique_together = ("id", "open_ts")
        db_table = "market_session"

    def __str__(self):
        return f'#{self.pk}: {self.status}'

