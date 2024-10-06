from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from ..common import create_user, login_user
from users.models.user_notification import UserNotification, UserNotificationType
import json


class TestUserNotificationUpdateStateAPIView(APITestCase):
    """
    Tests for UserNotificationUpdateStateAPIView class. This method should only be
    available to authenticated users.
    """

    def setUp(self):
        self.user = create_user()
        login_user(self.client, self.user)

        self.notification_type = UserNotificationType.objects.create(
            name='test-notification'
        )
        self.notification = UserNotification.objects.create(
            user=self.user,
            notification_type=self.notification_type,
            state=False
        )
        self.base_url = reverse('user:user-notification-update',
                                kwargs={'pk': self.notification.id})

    def test_update_notification_no_auth(self):
        self.client.credentials(HTTP_AUTHORIZATION="")
        response = self.client.put(f"{self.base_url}", data={'state': True})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_notification(self):
        response = self.client.put(f"{self.base_url}", data={'state': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.state)
        expected_response = {
            # 'id': self.notification.id,
            'state': True,
            # 'notification_type': self.notification.notification_type.name
        }
        self.assertEqual(response.json()['data'], expected_response)

    def test_update_notification_not_found(self):
        invalid_url_param = reverse('user:user-notification-update',
                                    kwargs={'pk': self.notification.id + 100})

        response = self.client.put(invalid_url_param, data={'state': True})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        expected_response = {
            'message': 'UserNotification matching query not found'
        }
        self.assertEqual(response.json()['data'], expected_response)

    def test_update_notification_invalid_data(self):

        data = {"ds": True}
        response = self.client.put(self.base_url,
                                   data=json.dumps(data),
                                   content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_response = {
            'state': [
                'This field is required.'
            ]
        }
        self.assertEqual(response.json()['data'], expected_response)
