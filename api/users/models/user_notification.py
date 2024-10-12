from django.db import models


class UserNotificationType(models.Model):
    objects = models.Manager()

    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class UserNotification(models.Model):
    objects = models.Manager()
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)
    notification_title = models.CharField(max_length=255)
    notification_description = models.CharField(max_length=255)
    notification_type = models.ForeignKey(UserNotificationType,
                                          on_delete=models.CASCADE)
    state = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user} - {self.notification_type}"
