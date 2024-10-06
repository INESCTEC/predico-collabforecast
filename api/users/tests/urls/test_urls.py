import uuid

from django.test import SimpleTestCase
from django.urls import reverse, resolve

from ...views.user import (
    RequestPasswordResetEmail,
    SetNewPassword,
    UserListView,
    UserRegisterView,
    UserVerifyEmailView)

from ...views.user_notification import (
    UserNotificationListAPIView,
    UserNotificationTypeDeleteAndUpdateAPIView,
    UserNotificationTypeListAndCreateAPIView,
    UserNotificationUpdateStateAPIView
)
from ...views.user_resources import (
    UserResourcesUpdateView,
    UserResourcesView)


class TestUrls(SimpleTestCase):

    def test_list_url_is_resolved(self):

        url = reverse('user:request-reset-email')
        self.assertEqual(resolve(url).func.view_class, RequestPasswordResetEmail)

        url = reverse('user:password-reset-complete')
        self.assertEqual(resolve(url).func.view_class, SetNewPassword)

        url = reverse('user:user-notification-list')
        self.assertEqual(resolve(url).func.view_class, UserNotificationListAPIView)

        url = reverse('user:user-notification-update', args=[1])
        self.assertEqual(resolve(url).func.view_class, UserNotificationUpdateStateAPIView)

        url = reverse('user:user-notification-type-list-create')
        self.assertEqual(resolve(url).func.view_class, UserNotificationTypeListAndCreateAPIView)

        url = reverse('user:user-notification-type-update-delete', args=[1])
        self.assertEqual(resolve(url).func.view_class, UserNotificationTypeDeleteAndUpdateAPIView)

        url = reverse('user:register')
        self.assertEqual(resolve(url).func.view_class, UserRegisterView)

        url = reverse('user:resource-list-create')
        self.assertEqual(resolve(url).func.view_class, UserResourcesView)

        url = reverse('user:resource-update', args=[uuid.uuid4()])
        self.assertEqual(resolve(url).func.view_class, UserResourcesUpdateView)

        url = reverse('user:user-list')
        self.assertEqual(resolve(url).func.view_class, UserListView)
