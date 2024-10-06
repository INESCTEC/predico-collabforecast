from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from ..common import create_user, login_user
from users.models.user_notification import UserNotification


class TestUserNotificationListView(APITestCase):
    """
    Tests for UserNotificationListView class. This method should only be
    available to authenticated users.
    """

    def setUp(self):
        self.base_url = reverse("user:user-notification-list")
        self.normal_user = create_user()
        login_user(self.client, self.normal_user)

    def test_list_notifications_no_auth(self):

        self.client.credentials(HTTP_AUTHORIZATION="")
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_notifications(self):
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()["data"]
        self.assertEqual(len(response_data),
                         UserNotification.objects.filter(user=self.normal_user).count())
