import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from ..managers import CustomUserManager


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    username = None
    email = models.EmailField(_('email address'), unique=True)
    # Auth
    is_verified = models.BooleanField(default=False)
    # Is session manager (allows create/update market sessions)
    is_session_manager = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    # the object returned when created
    def __str__(self):
        return self.email


class OneTimeToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=500)
    used = models.BooleanField(default=False)
    expiration_time = models.DateTimeField()
