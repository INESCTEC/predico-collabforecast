# ruff: noqa: E501
from dataclasses import dataclass
from typing import List, Tuple

from users.models import UserNotification, UserNotificationType


# if you want to add
@dataclass
class NotificationData:
    name: str
    descriptions: List[Tuple[str, str]]


notifications = [
    NotificationData(
        name='bid',
        descriptions=[
            ('New bid', 'Bid has been received'),
            ('Validation bid', 'Bid has been validated')
        ]
    ),
    NotificationData(
        name='session',
        descriptions=[
            ('New session', 'A new session is available'),
            ('Session results', 'Results for a session are available')
        ]
    ),
    NotificationData(
        name='market',
        descriptions=[
            ('Market update', 'There is an update for the market'),
            ('Market transaction', 'A transaction from the market for you has been made')
        ]
    ),
    NotificationData(
        name='forecast',
        descriptions=[
            ('New forecast', 'A new forecast is available for one or more of your resources')
        ]
    ),
    NotificationData(
        name='data',
        descriptions=[
            ('Data correctly received', 'The market validated the reception of data sent for one of your resources'),
            ('Data incorrectly received', 'An error occurred with the data sent for one of your resources')
        ]
    )
]


def create_user_notifications(user):

    for notification_data in notifications:
        notification_type, _ = UserNotificationType.objects.get_or_create(name=notification_data.name)
        for notification_title, notification_description in notification_data.descriptions:
            UserNotification.objects.create(
                user=user,
                notification_type=notification_type,
                notification_title=notification_title,
                notification_description=notification_description
            )
