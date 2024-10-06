from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from ..common import create_and_login_superuser, create_user, login_user
from users.models.user_notification import UserNotificationType, UserNotification
from users.models.user import User


class TestUserNotificationTypeAPIView(APITestCase):
    """
    Tests for UserNotificationTypeListAndCreateAPIView and
    UserNotificationTypeDeleteAndUpdateAPIView views.
    This method should only be available to admin users.
    """

    def setUp(self):
        self.admin_user = create_and_login_superuser(self.client)
        self.normal_user = create_user()
        self.notification_type = UserNotificationType.objects.create(
            name='test-notification-type'
        )
        self.list_create_url = reverse('user:user-notification-type-list-create')
        self.update_url = reverse('user:user-notification-type-update-delete',
                                  kwargs={'pk': self.notification_type.id})
        self.delete_url = reverse('user:user-notification-type-update-delete',
                                  kwargs={'pk': self.notification_type.id})

    def test_list_notification_types_no_auth(self):
        self.client.credentials(HTTP_AUTHORIZATION="")
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_notification_types(self):
        login_user(self.client, self.admin_user)
        current_notifications_types = UserNotificationType.objects.all().count()
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()['data']["results"]), current_notifications_types)

    def test_create_notification_type_no_auth(self):
        self.client.credentials(HTTP_AUTHORIZATION="")
        response = self.client.post(self.list_create_url,
                                    data={'name': 'new-notification-type'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_notification_type(self):
        login_user(self.client, user=self.admin_user)
        response = self.client.post(self.list_create_url,
                                    data={'name': 'another-new-random-notification'})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserNotificationType.objects.last().name,
                         'another-new-random-notification')

        notification_type_id = response.json()['data']['id']

        # Test if the newly created notification type was created for all users
        for user in User.objects.all():
            self.assertTrue(UserNotification.objects.filter(
                user=user,
                notification_type=notification_type_id).exists())

    def test_create_similar_notification_type(self):
        login_user(self.client, user=self.admin_user)
        response = self.client.post(self.list_create_url,
                                    data=({'name': 'test-notification-type-2'}))
        expected_response = {
            'name': ['Similar notification event already exists']
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['data'], expected_response)

    def test_create_notification_type_normal_user(self):
        login_user(self.client, self.normal_user)
        response = self.client.post(self.list_create_url,
                                    data={'name': 'new-notification-type'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_notification_type_no_auth(self):
        self.client.credentials(HTTP_AUTHORIZATION="")
        response = self.client.put(self.update_url,
                                   data={'name': 'updated-notification-type'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_notification_type(self):
        login_user(self.client, self.admin_user)
        response = self.client.put(self.update_url,
                                   data={'name': 'updated-app-forecast-notification'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification_type.refresh_from_db()
        self.assertEqual(self.notification_type.name,
                         'updated-app-forecast-notification')

    def test_update_notification_type_normal_user(self):
        login_user(self.client, self.normal_user)
        response = self.client.put(self.update_url,
                                   data={'name': 'updated-notification-type'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_notification_type_not_found(self):
        login_user(self.client, self.admin_user)
        url_param = reverse('user:user-notification-type-update-delete',
                            kwargs={'pk': self.notification_type.id + 100})
        response = self.client.put(url_param,
                                   data={'name': 'updated-notification-type'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_response = {
            'message': 'UserNotificationType matching query does not exist'
        }
        self.assertEqual(response.json()['data'], expected_response)

    def test_delete_notification_type_no_auth(self):
        self.client.credentials(HTTP_AUTHORIZATION="")
        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_notification_type(self):
        login_user(self.client, self.admin_user)
        current_number_of_notifications = UserNotificationType.objects.count()
        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(UserNotificationType.objects.count(),
                         current_number_of_notifications - 1)

    def test_delete_notification_type_normal_user(self):
        login_user(self.client, self.normal_user)
        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_notification_type_not_found(self):
        login_user(self.client, self.admin_user)
        invalid_url_param = reverse('user:user-notification-type-update-delete',
                                    kwargs={'pk': self.notification_type.id + 100})
        response = self.client.delete(invalid_url_param)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_response = {
            'message': 'UserNotificationType matching query does not exist'
        }
        self.assertEqual(response.json()['data'], expected_response)
