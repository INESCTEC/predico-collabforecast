import uuid

from django.test import SimpleTestCase
from django.urls import reverse, resolve

from ...views.user import (UserListView, UserRegisterView)
from ...views.user_reset_password import (PasswordResetView, PasswordResetRequestView)
from ...views.user_resources import (
    UserResourcesUpdateView,
    UserResourcesView)


class TestUrls(SimpleTestCase):

    def test_list_url_is_resolved(self):

        url = reverse('user:password-reset-request')
        self.assertEqual(resolve(url).func.view_class, PasswordResetRequestView)

        url = reverse('user:password-reset-confirm')
        self.assertEqual(resolve(url).func.view_class, PasswordResetView)


        url = reverse('user:register')
        self.assertEqual(resolve(url).func.view_class, UserRegisterView)

        url = reverse('user:resource-list-create')
        self.assertEqual(resolve(url).func.view_class, UserResourcesView)

        url = reverse('user:resource-update', args=[uuid.uuid4()])
        self.assertEqual(resolve(url).func.view_class, UserResourcesUpdateView)

        url = reverse('user:user-list')
        self.assertEqual(resolve(url).func.view_class, UserListView)
